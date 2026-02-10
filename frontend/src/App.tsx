import React, { useState, useEffect } from 'react';
import { AuthState, ModalType, SummaryResult, SummarySize, Language } from './types';
import { checkAuthStatus, logoutUser, extractSummary } from './services/api';
import { Mascot } from './components/Mascot';
import { AmpSlider } from './components/AmpSlider';
import { ActionBurst } from './components/ActionBurst';
import { AuthModal } from './components/AuthModal';
import { ResultPanel } from './components/ResultPanel';
import { Library } from './components/Library';
import { LogOut, User as UserIcon, BookOpen, Home } from 'lucide-react';

const App: React.FC = () => {
    const [auth, setAuth] = useState<AuthState>({ isAuthenticated: false, user: null });
    const [url, setUrl] = useState('');
    const [size, setSize] = useState<SummarySize>(SummarySize.MEDIUM);
    const [language, setLanguage] = useState<Language>('EN');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [modal, setModal] = useState<ModalType>('none');
    const [result, setResult] = useState<SummaryResult | null>(null);

    // Router State
    const [view, setView] = useState<'home' | 'library'>('home');

    // Check authentication status on app initialization
    const isAuthChecked = React.useRef(false);
    useEffect(() => {
        if (isAuthChecked.current) return;
        isAuthChecked.current = true;

        const restoreAuthState = async () => {
            try {
                const user = await checkAuthStatus();
                if (user) {
                    setAuth({ isAuthenticated: true, user });
                }
            } catch (error) {
                // Authentication check failed, user remains logged out
                console.log('Authentication check failed:', error);
            }
        };

        restoreAuthState();
    }, []);

    const handleAuthSuccess = (user: any) => {
        setAuth({ isAuthenticated: true, user });
        setModal('none');
    };

    const handleLogout = async () => {
        // Clear the authentication token
        await logoutUser();

        // Clear local state
        setAuth({ isAuthenticated: false, user: null });
        setResult(null);
        setUrl('');
        setView('home'); // Go home on logout
    };

    const handleExtract = async () => {
        setError(null);

        // 1. Auth Check
        if (!auth.isAuthenticated) {
            setModal('register'); // Default to register for new users, or prompt login
            return;
        }

        // 2. Validation
        if (!url.trim()) {
            setError("NO DATA DETECTED. FEED THE MACHINE.");
            return;
        }

        // 3. Process
        setIsLoading(true);
        try {
            const data = await extractSummary(url, size, language);
            setResult(data);
            setModal('result');
        } catch (err: any) {
            setError(err.message || "UNKNOWN ERROR IN THE VOID.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#f3f4f6] text-black overflow-x-hidden font-terminal relative">

            {/* Background Halftone Noise */}
            <div className="fixed inset-0 pointer-events-none bg-comic-noise opacity-30 z-0"></div>

            {/* Header / Nav */}
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
                            px-4 py-2 font-marker text-xl border-4 border-black transition-all shadow-[4px_4px_0px_0px_#000] hover:translate-y-1 hover:shadow-none flex items-center gap-2
                            ${view === 'home' ? 'bg-yellow-400 rotate-1' : 'bg-white hover:bg-gray-100 -rotate-1'}
                        `}
                            >
                                <Home size={20} /> HOME
                            </button>
                            <button
                                onClick={() => setView('library')}
                                className={`
                            px-4 py-2 font-marker text-xl border-4 border-black transition-all shadow-[4px_4px_0px_0px_#000] hover:translate-y-1 hover:shadow-none flex items-center gap-2
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

            {/* View Routing */}
            {view === 'library' && auth.isAuthenticated ? (
                <Library />
            ) : (
                <main className="relative z-10 container mx-auto px-4 md:px-8 flex flex-col md:flex-row items-center justify-center min-h-[calc(100vh-150px)]">
                    {/* Left Column: Mascot (Desktop) / Top (Mobile) */}
                    <div className="w-full md:w-1/2 flex justify-center md:justify-end order-1 md:order-1">
                        <Mascot />
                    </div>

                    {/* Right Column: Controls */}
                    <div className="w-full md:w-1/2 max-w-lg mt-8 md:mt-0 order-2 md:order-2 pb-12">
                        <div className="bg-white p-8 border-4 border-black shadow-[12px_12px_0px_0px_rgba(76,29,149,1)] relative transform md:rotate-1">

                            {/* Decorative Screw Heads */}
                            <div className="absolute top-2 left-2 w-4 h-4 rounded-full border-2 border-gray-400 flex items-center justify-center"><div className="w-full h-[1px] bg-gray-400 rotate-45"></div></div>
                            <div className="absolute top-2 right-2 w-4 h-4 rounded-full border-2 border-gray-400 flex items-center justify-center"><div className="w-full h-[1px] bg-gray-400 rotate-45"></div></div>
                            <div className="absolute bottom-2 left-2 w-4 h-4 rounded-full border-2 border-gray-400 flex items-center justify-center"><div className="w-full h-[1px] bg-gray-400 rotate-45"></div></div>
                            <div className="absolute bottom-2 right-2 w-4 h-4 rounded-full border-2 border-gray-400 flex items-center justify-center"><div className="w-full h-[1px] bg-gray-400 rotate-45"></div></div>

                            {/* Language Switcher & URL Label */}
                            <div className="mb-8">
                                <div className="flex justify-between items-end mb-2">
                                    <label className="font-marker text-2xl transform -skew-x-6 inline-block bg-black text-white px-2">
                                        YOUTUBE VIDEO
                                    </label>

                                    {/* Brutalist Language Toggle */}
                                    <div className="flex border-4 border-black shadow-[4px_4px_0px_0px_#000] bg-white transform -rotate-2">
                                        <button
                                            onClick={() => setLanguage('EN')}
                                            className={`px-3 py-1 font-bold font-marker text-xl transition-all ${language === 'EN' ? 'bg-yellow-400 text-black' : 'text-gray-400 hover:text-black hover:bg-gray-100'}`}
                                        >
                                            EN
                                        </button>
                                        <div className="w-1 bg-black"></div>
                                        <button
                                            onClick={() => setLanguage('RU')}
                                            className={`px-3 py-1 font-bold font-marker text-xl transition-all ${language === 'RU' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-black hover:bg-gray-100'}`}
                                        >
                                            RU
                                        </button>
                                    </div>
                                </div>

                                <div className="relative">
                                    <input
                                        type="text"
                                        value={url}
                                        onChange={(e) => setUrl(e.target.value)}
                                        placeholder="https://youtube.com/watch?v=..."
                                        className="w-full bg-gray-100 border-4 border-black p-4 font-terminal text-2xl focus:bg-yellow-50 outline-none placeholder:text-gray-400 transition-all focus:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
                                    />
                                </div>
                            </div>

                            {/* Slider */}
                            <AmpSlider value={size} onChange={setSize} disabled={isLoading} />

                            {/* Error Display */}
                            {error && (
                                <div className="my-4 p-3 bg-red-100 border-l-8 border-red-600 font-terminal text-xl text-red-700 font-bold animate-pulse">
                                    ERROR: {error}
                                </div>
                            )}

                            {/* Big Button */}
                            <div className="flex justify-center mt-10">
                                <ActionBurst
                                    onClick={handleExtract}
                                    isLoading={isLoading}
                                    text="EXTRACT"
                                />
                            </div>
                        </div>
                    </div>
                </main>
            )}

            {/* Modals */}
            {(modal === 'login' || modal === 'register') && (
                <AuthModal
                    initialMode={modal}
                    onClose={() => setModal('none')}
                    onSuccess={handleAuthSuccess}
                />
            )}

            {modal === 'result' && result && (
                <ResultPanel
                    result={result}
                    onClose={() => setModal('none')}
                    mode="preview"
                />
            )}

        </div>
    );
};

export default App;