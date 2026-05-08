import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { fetchApiMeta } from '../services/api';
import { jwtDecode } from "jwt-decode"; // <-- IMPORTANTE: Agregamos esto

export default function Login({ addToast }: { addToast: (message: string, type?: 'success' | 'error' | 'info') => void }) {
  const { user, loginWithGoogle } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) navigate('/');
  }, [user, navigate]);

  useEffect(() => {
    (async () => {
      const meta = await fetchApiMeta();
      if (!meta) {
        addToast('No hay respuesta válida del backend', 'error');
      }
    })();

    // Inicializar el botón de Google cuando el script cargue
    const scriptId = 'google-identity';
    if (!document.getElementById(scriptId)) {
      const s = document.createElement('script');
      s.src = 'https://accounts.google.com/gsi/client';
      s.id = scriptId;
      s.async = true;
      s.defer = true;
      document.head.appendChild(s);
      s.onload = () => renderButton();
    } else {
      renderButton();
    }

    function renderButton() {
      // @ts-ignore
      if (!window.google || !window.google.accounts) return;

      const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
      if (!clientId) {
        addToast('VITE_GOOGLE_CLIENT_ID no configurado en frontend', 'error');
        return;
      }

      // @ts-ignore
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: (resp: any) => {
          if (resp?.credential) {

            // --- INICIO DE LA VALIDACIÓN DEL DOMINIO ---
            try {
              const decodedToken: any = jwtDecode(resp.credential);
              const userEmail = decodedToken.email;

              if (!userEmail.endsWith('@virtual.upt.pe')) {
                addToast('Acceso denegado: Usa tu correo institucional @virtual.upt.pe', 'error');
                return; // Cortamos la ejecución aquí, no iniciamos sesión
              }
            } catch (error) {
              addToast('Error al procesar los datos de Google', 'error');
              return;
            }
            // --- FIN DE LA VALIDACIÓN ---

            // Si pasa la validación, procedemos con tu lógica original
            loginWithGoogle(resp.credential).then(() => {
              addToast('Sesión iniciada con Google', 'success');
              navigate('/');
            }).catch((err: Error) => {
              addToast(err.message || 'Login failed', 'error');
            });
          } else {
            addToast('Google login no devolvió credencial', 'error');
          }
        },
      });
      // @ts-ignore
      window.google.accounts.id.renderButton(document.getElementById('gsi-btn'), { theme: 'outline', size: 'large' });
    }

    return () => { };
  }, [addToast, loginWithGoogle, navigate]);

  return (
    <div className="page-content" style={{ maxWidth: 440, margin: '0 auto' }}>
      <div className="card">
        <div className="card-header">
          <h2>Iniciar sesión con Google</h2>
          <p>Usa tu cuenta institucional (@virtual.upt.pe) para continuar.</p>
        </div>
        <div style={{ padding: '16px', display: 'flex', justifyContent: 'center' }}>
          <div id="gsi-btn" />
        </div>
      </div>
    </div>
  );
}