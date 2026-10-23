import java.net.InetSocketAddress;
import java.net.Socket;
import java.security.KeyStore;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLEngine;
import javax.net.ssl.SSLParameters;
import javax.net.ssl.SSLSocket;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.TrustManagerFactory;
import javax.net.ssl.X509ExtendedTrustManager;

/**
 * Connects to each host with the JVM's default TLS settings and trust store.
 *
 * Usage: java BlockedCertsProbe.java --blocked host... --allowed host...
 *
 * A --blocked host passes if the handshake fails because a certificate is in blocked.certs, or because this JVM
 * trusts none of the certificates' issuers (so the chain can never be accepted). Any other outcome fails, including
 * a successful connection or a network error. An --allowed host passes if the handshake succeeds.
 */
public class BlockedCertsProbe {
    private static final int TIMEOUT_MILLIS = 15_000;

    public static void main(String[] args) throws Exception {
        List<String> blocked = new ArrayList<>();
        List<String> allowed = new ArrayList<>();
        List<String> current = null;
        for (String arg : args) {
            if (arg.equals("--blocked")) {
                current = blocked;
            } else if (arg.equals("--allowed")) {
                current = allowed;
            } else if (current == null) {
                throw new IllegalArgumentException("Expected --blocked or --allowed before " + arg);
            } else {
                current.add(arg);
            }
        }

        System.out.println("java.home=" + System.getProperty("java.home") + " java.runtime.version=" + System.getProperty("java.runtime.version"));
        X509ExtendedTrustManager defaultTrustManager = defaultTrustManager();
        Set<String> trustedSubjects = new HashSet<>();
        for (X509Certificate certificate : defaultTrustManager.getAcceptedIssuers()) {
            trustedSubjects.add(certificate.getSubjectX500Principal().getName());
        }
        int failures = 0;
        int blockedByList = 0;
        for (String host : blocked) {
            RecordingTrustManager trustManager = new RecordingTrustManager(defaultTrustManager);
            SSLContext context = SSLContext.getInstance("TLS");
            context.init(null, new TrustManager[]{trustManager}, null);
            Throwable error = connect(host, context.getSocketFactory());
            String message = error == null ? "" : String.valueOf(rootCause(error).getMessage());
            if (error == null) {
                failures++;
                System.out.println("FAIL    " + host + ": connected, expected the certificate chain to be rejected");
            } else if (message.contains("Untrusted certificate")) {
                blockedByList++;
                System.out.println("OK      " + host + ": rejected, " + message);
            } else if (message.contains("unable to find valid certification path")) {
                String trusted = trustedIssuer(trustManager.chain, trustedSubjects);
                if (trusted == null) {
                    System.out.println("OK      " + host + ": rejected, no trusted issuer in this JVM's trust store");
                } else {
                    failures++;
                    System.out.println("FAIL    " + host + ": rejected with '" + message + "', but the trust store has " + trusted);
                }
            } else {
                failures++;
                System.out.println("FAIL    " + host + ": " + rootCause(error));
            }
        }
        if (!blocked.isEmpty() && blockedByList == 0) {
            failures++;
            System.out.println("FAIL    no connection was rejected by blocked.certs, so the test did not exercise it");
        }
        for (String host : allowed) {
            Throwable error = connect(host, (SSLSocketFactory) SSLSocketFactory.getDefault());
            if (error == null) {
                System.out.println("OK      " + host + ": connected");
            } else {
                failures++;
                System.out.println("FAIL    " + host + ": " + rootCause(error));
            }
        }
        if (failures > 0) {
            System.out.println(failures + " check(s) failed");
            System.exit(1);
        }
    }

    private static Throwable connect(String host, SSLSocketFactory factory) {
        try (Socket plain = new Socket()) {
            plain.connect(new InetSocketAddress(host, 443), TIMEOUT_MILLIS);
            plain.setSoTimeout(TIMEOUT_MILLIS);
            try (SSLSocket socket = (SSLSocket) factory.createSocket(plain, host, 443, false)) {
                SSLParameters parameters = socket.getSSLParameters();
                parameters.setEndpointIdentificationAlgorithm("HTTPS");
                socket.setSSLParameters(parameters);
                socket.startHandshake();
            }
            return null;
        } catch (Exception e) {
            return e;
        }
    }

    // Returns the first issuer in the chain the server sent that the default trust store has.
    private static String trustedIssuer(List<X509Certificate> chain, Set<String> trustedSubjects) {
        if (chain.isEmpty()) {
            return "an unknown issuer (the server sent no chain)";
        }
        for (X509Certificate certificate : chain) {
            String issuer = certificate.getIssuerX500Principal().getName();
            if (trustedSubjects.contains(issuer)) {
                return issuer;
            }
        }
        return null;
    }

    private static X509ExtendedTrustManager defaultTrustManager() throws Exception {
        TrustManagerFactory factory = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
        factory.init((KeyStore) null);
        for (TrustManager manager : factory.getTrustManagers()) {
            if (manager instanceof X509ExtendedTrustManager) {
                return (X509ExtendedTrustManager) manager;
            }
        }
        throw new IllegalStateException("No X509ExtendedTrustManager in the default TrustManagerFactory");
    }

    private static Throwable rootCause(Throwable error) {
        while (error.getCause() != null) {
            error = error.getCause();
        }
        return error;
    }

    // Records the chain the server sends, then leaves every decision to the default trust manager.
    private static class RecordingTrustManager extends X509ExtendedTrustManager {
        private final X509ExtendedTrustManager delegate;
        private final List<X509Certificate> chain = new ArrayList<>();

        RecordingTrustManager(X509ExtendedTrustManager delegate) {
            this.delegate = delegate;
        }

        @Override
        public void checkServerTrusted(X509Certificate[] certificates, String authType, Socket socket) throws CertificateException {
            chain.addAll(List.of(certificates));
            delegate.checkServerTrusted(certificates, authType, socket);
        }

        @Override
        public void checkServerTrusted(X509Certificate[] certificates, String authType, SSLEngine engine) throws CertificateException {
            chain.addAll(List.of(certificates));
            delegate.checkServerTrusted(certificates, authType, engine);
        }

        @Override
        public void checkServerTrusted(X509Certificate[] certificates, String authType) throws CertificateException {
            chain.addAll(List.of(certificates));
            delegate.checkServerTrusted(certificates, authType);
        }

        @Override
        public void checkClientTrusted(X509Certificate[] certificates, String authType, Socket socket) throws CertificateException {
            delegate.checkClientTrusted(certificates, authType, socket);
        }

        @Override
        public void checkClientTrusted(X509Certificate[] certificates, String authType, SSLEngine engine) throws CertificateException {
            delegate.checkClientTrusted(certificates, authType, engine);
        }

        @Override
        public void checkClientTrusted(X509Certificate[] certificates, String authType) throws CertificateException {
            delegate.checkClientTrusted(certificates, authType);
        }

        @Override
        public X509Certificate[] getAcceptedIssuers() {
            return delegate.getAcceptedIssuers();
        }
    }
}
