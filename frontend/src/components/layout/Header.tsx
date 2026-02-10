import React from 'react';
import { LogOut, User as UserIcon, BookOpen, Home } from 'lucide-react';
import { AuthState, ModalType } from '../../types';

interface HeaderProps {
    auth: AuthState;
    view: 'home' | 'library';
    setView: (view: 'home' | 'library') => void;
    handleLogout: () => void;
    setModal: (modal: ModalType) => void;
}

export const Header: React.FC<HeaderProps> = ({
    auth,
    view,
    setView,
    handleLogout,
    setModal
}) => {
    return (
        <nav className="relative z-40 p-4 md:p-6 flex flex-col md:flex-row justify-between items-center gap-4 bg-white/50 backdrop-blur-sm border-b-2 border-transparent">
            <div
                className="transform -rotate-2 cursor-pointer group"
                onClick={() => setView('home')}
            >
                <h1 className="font-marker text-4xl md:text-6xl text-black drop-shadow-[4px_4px_0px_#FACC15] group-hover:drop-shadow-[6px_6px_0px_#FACC15] transition-all">
                    WATABAUTET
                </h1>
                <p className="font-terminal text-lg md:text-xl text-purple-900 font-bold bg-yellow-400 inline-block px-2">
                    THE ESSENCE EXTRACTOR
                </p>
            </div>

            <div className="flex flex-col md:flex-row items-center gap-4">
                {/* Navigation Menu (Only if Auth) */}
                {auth.isAuthenticated && (
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setView('home')}
                            className={`
                        px-4 py-2 font-marker text-xl brutalist-border transition-all brutalist-shadow hover:translate-y-1 hover:shadow-none flex items-center gap-2
                        ${view === 'home' ? 'bg-yellow-400 rotate-1' : 'bg-white hover:bg-gray-100 -rotate-1'}
                    `}
                        >
                            <Home size={20} /> HOME
                        </button>
                        <button
                            onClick={() => setView('library')}
                            className={`
                        px-4 py-2 font-marker text-xl brutalist-border transition-all brutalist-shadow hover:translate-y-1 hover:shadow-none flex items-center gap-2
                        ${view === 'library' ? 'bg-purple-400 text-white rotate-1' : 'bg-white hover:bg-gray-100 -rotate-1'}
                    `}
                        >
                            <BookOpen size={20} /> LIBRARY
                        </button>
                    </div>
                )}

                {/* User Controls */}
                {auth.isAuthenticated ? (
                    <div className="flex items-center gap-4 bg-white border-2 border-black p-2 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                        <div className="flex items-center gap-2 font-bold text-lg">
                            <UserIcon size={20} className="text-purple-800" />
                            <span className="uppercase">{auth.user?.username}</span>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="bg-black text-white hover:bg-red-600 p-1 transition-colors"
                            title="Disconnect"
                        >
                            <LogOut size={20} />
                        </button>
                    </div>
                ) : (
                    <button
                        onClick={() => setModal('login')}
                        className="font-marker text-xl underline decoration-wavy decoration-purple-600 hover:text-purple-800 transition-colors"
                    >
                        [ LOGIN_ACCESS ]
                    </button>
                )}
            </div>
        </nav>
    );
};
