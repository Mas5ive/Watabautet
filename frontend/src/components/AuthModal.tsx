import React, { useState } from 'react';
import { User } from '../types';
import { loginUser, registerUser } from '../services/api';
import { AlertTriangle, User as UserIcon, Lock } from 'lucide-react';

interface AuthModalProps {
  initialMode: 'login' | 'register';
  onSuccess: (user: User) => void;
  onClose: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ initialMode, onSuccess, onClose }) => {
  const [mode, setMode] = useState(initialMode);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      let user: User;
      if (mode === 'login') {
        user = await loginUser(username, password);
      } else {
        user = await registerUser(username, password);
      }
      onSuccess(user);
    } catch (err: any) {
      setError(err.message || "SYSTEM FAILURE.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-purple-900/80 backdrop-grayscale p-4">
      <div className="bg-white w-full max-w-md border-4 border-black p-8 relative shadow-[20px_20px_0px_0px_#000]">

        {/* Decorative Tape */}
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 w-32 h-8 bg-yellow-400/90 rotate-2 border-l-2 border-r-2 border-white/50"></div>

        <h2 className="text-4xl font-marker text-center mb-8 uppercase transform -rotate-2">
          {mode === 'login' ? 'Identify Yourself' : 'Join The Resistance'}
        </h2>

        {error && (
          <div className="mb-6 bg-red-100 border-2 border-red-600 p-3 flex items-start gap-2 font-terminal text-red-600 font-bold">
            <AlertTriangle className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="relative group">
            <label className="block font-marker mb-2 text-xl">USERNAME ID</label>
            <div className="relative">
              <UserIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 group-focus-within:text-black" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-gray-100 border-b-4 border-gray-400 focus:border-black outline-none py-3 pl-12 pr-4 font-terminal text-2xl transition-colors"
                placeholder="ENTER ALIAS..."
                required
              />
            </div>
          </div>

          <div className="relative group">
            <label className="block font-marker mb-2 text-xl">PASSWORD</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 group-focus-within:text-black" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-gray-100 border-b-4 border-gray-400 focus:border-black outline-none py-3 pl-12 pr-4 font-terminal text-2xl transition-colors"
                placeholder="ENTER PASSWORD..."
                minLength={8}
                required
              />
            </div>
            {mode === 'register' && (
              <p className="text-sm text-gray-600 mt-1 font-terminal">
                Minimum 8 characters required
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-black text-yellow-400 font-marker text-2xl py-4 hover:bg-yellow-400 hover:text-black transition-colors border-4 border-transparent hover:border-black"
          >
            {isLoading ? 'ACCESSING...' : (mode === 'login' ? 'ENTER SYSTEM' : 'CREATE ACCOUNT')}
          </button>
        </form>

        <div className="mt-6 text-center font-terminal text-lg">
          {mode === 'login' ? (
            <>
              New Unit? <button onClick={() => { setMode('register'); setPassword(''); }} className="underline decoration-wavy decoration-purple-600 text-purple-800 font-bold">Register Protocol</button>
            </>
          ) : (
            <>
              Existing Unit? <button onClick={() => { setMode('login'); setPassword(''); }} className="underline decoration-wavy decoration-purple-600 text-purple-800 font-bold">Login Protocol</button>
            </>
          )}
        </div>

        <button onClick={onClose} className="absolute top-2 right-2 font-marker text-xl hover:text-red-600">X</button>
      </div>
    </div>
  );
};