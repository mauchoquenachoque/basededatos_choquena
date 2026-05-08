import { FormEvent, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { fetchApiMeta, RESOLVED_API_BASE } from '../services/api';

type Mode = 'login' | 'register';

export default function Login({ addToast }: { addToast: (message: string, type?: 'success' | 'error' | 'info') => void }) {
  const { user, login, signUp } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [backendWarning, setBackendWarning] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      navigate('/');
    }
  }, [user, navigate]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const meta = await fetchApiMeta();
      if (cancelled) return;
      if (!meta) {
        setBackendWarning(
          `No hay respuesta válida en ${RESOLVED_API_BASE}/meta. Arranca el backend desde la carpeta backend con el código actual (git pull), o ejecuta .\\scripts\\start-local.ps1 desde la raíz del proyecto.`,
        );
        return;
      }
      if (meta.service !== 'enmask-backend') {
        setBackendWarning(
          `En el puerto del API hay otro programa (no es Enmask). Cierra ese proceso y levanta este proyecto desde la carpeta backend. Respuesta: service=${meta.service ?? '?'}`,
        );
      } else if (meta.auth && meta.auth !== 'email_password') {
        setBackendWarning('Este backend no usa login por correo/contraseña. Usa la versión del repo EnmascaradoDatos.');
      } else {
        setBackendWarning(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      if (mode === 'register') {
        await signUp(email, password, name);
        addToast('Cuenta creada. Bienvenido.', 'success');
      } else {
        await login(email, password);
        addToast('Sesión iniciada.', 'success');
      }
      navigate('/');
    } catch (err) {
      addToast((err as Error).message || 'Error', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page-content" style={{ maxWidth: 440, margin: '0 auto' }}>
      <div className="card">
        <div className="card-header">
          <h2>{mode === 'login' ? 'Iniciar sesión' : 'Crear cuenta'}</h2>
          <p>
            {mode === 'login'
              ? 'Entra con el correo y la contraseña que usaste al registrarte.'
              : 'Regístrate para guardar conexiones y reglas en tu espacio.'}
          </p>
        </div>
        <div style={{ padding: '8px 16px 20px' }}>
          {backendWarning && (
            <div
              role="alert"
              style={{
                marginBottom: 16,
                padding: '12px 14px',
                borderRadius: 8,
                background: 'rgba(244,63,94,0.12)',
                border: '1px solid rgba(244,63,94,0.35)',
                color: 'var(--text-primary)',
                fontSize: 13,
                lineHeight: 1.45,
              }}
            >
              {backendWarning}
            </div>
          )}
          <div
            role="tablist"
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 8,
              marginBottom: 20,
            }}
          >
            <button
              type="button"
              className={`btn ${mode === 'login' ? '' : 'btn-clear'}`}
              onClick={() => setMode('login')}
            >
              Entrar
            </button>
            <button
              type="button"
              className={`btn ${mode === 'register' ? '' : 'btn-clear'}`}
              onClick={() => setMode('register')}
            >
              Registrarse
            </button>
          </div>

          <form onSubmit={onSubmit} style={{ display: 'grid', gap: 14 }}>
            {mode === 'register' && (
              <div className="form-group">
                <label htmlFor="reg-name">Nombre</label>
                <input
                  id="reg-name"
                  type="text"
                  autoComplete="name"
                  value={name}
                  onChange={(ev) => setName(ev.target.value)}
                  placeholder="Tu nombre"
                  required
                  minLength={1}
                  maxLength={120}
                />
              </div>
            )}
            <div className="form-group">
              <label htmlFor="auth-email">Correo</label>
              <input
                id="auth-email"
                type="email"
                autoComplete={mode === 'login' ? 'email' : 'username'}
                value={email}
                onChange={(ev) => setEmail(ev.target.value)}
                placeholder="correo@ejemplo.com"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="auth-password">Contraseña</label>
              <input
                id="auth-password"
                type="password"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                value={password}
                onChange={(ev) => setPassword(ev.target.value)}
                placeholder={mode === 'register' ? 'Mínimo 8 caracteres' : '••••••••'}
                required
                minLength={mode === 'register' ? 8 : 1}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={isLoading} style={{ marginTop: 8 }}>
              {isLoading ? 'Espera…' : mode === 'login' ? 'Entrar' : 'Crear cuenta'}
            </button>
          </form>
          {isLoading && <div className="spinner" style={{ margin: '16px auto 0' }} />}
        </div>
      </div>
    </div>
  );
}
