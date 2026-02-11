import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';

const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const isStrongPassword = (value: string) => {
  const hasLetter = /[A-Za-z]/.test(value);
  const hasNumber = /[0-9]/.test(value);
  return value.length >= 8 && hasLetter && hasNumber;
};

export default function AcceptInvitation() {
  const [params] = useSearchParams();
  const token = params.get('token') || '';
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const passwordOk = useMemo(() => isStrongPassword(password), [password]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');

    if (!token) {
      setError('Invitation token is missing.');
      return;
    }
    if (!passwordOk) {
      setError('Password must be at least 8 characters and include letters and numbers.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }

    try {
      await axios.post(`${apiBaseUrl}/users/accept-invitation`, {
        token,
        password,
        full_name: fullName || null,
      });
      setSuccess('Invitation accepted. Redirecting to login...');
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      setError('Failed to accept invitation. The token may be invalid or expired.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg">
      <div className="w-full max-w-md p-8 glass rounded-2xl shadow-2xl border border-white/10 mx-4">
        <h1 className="text-2xl font-bold text-white mb-2">Accept Invitation</h1>
        <p className="text-slate-400 mb-6">Set your password to join the Beehus Platform.</p>

        {error && <div className="p-3 rounded bg-red-500/20 text-red-300 text-sm mb-4">{error}</div>}
        {success && <div className="p-3 rounded bg-green-500/20 text-green-300 text-sm mb-4">{success}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            className="w-full px-4 py-3 bg-dark-bg/50 border border-dark-border rounded-lg text-white"
            placeholder="Full name (optional)"
          />
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full px-4 py-3 bg-dark-bg/50 border border-dark-border rounded-lg text-white"
            placeholder="Password"
          />
          <div className={`text-xs ${passwordOk ? 'text-green-400' : 'text-slate-500'}`}>
            Use at least 8 characters with letters and numbers.
          </div>
          <input
            type="password"
            value={confirm}
            onChange={(event) => setConfirm(event.target.value)}
            className="w-full px-4 py-3 bg-dark-bg/50 border border-dark-border rounded-lg text-white"
            placeholder="Confirm password"
          />
          <button
            type="submit"
            className="w-full py-3 bg-brand-600 hover:bg-brand-500 text-white rounded-lg font-semibold"
          >
            Accept Invitation
          </button>
        </form>
      </div>
    </div>
  );
}
