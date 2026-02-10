import React, { useState, useEffect, useCallback } from 'react';
import { AuthState, ModalType, SummaryResult, SummarySize, Language } from './types';
import { checkAuthStatus, logoutUser, extractSummary } from './services/api';
import { Mascot } from './components/Mascot';
import { AmpSlider } from './components/AmpSlider';
import { ActionBurst } from './components/ActionBurst';
import { AuthModal } from './components/AuthModal';
import { ResultPanel } from './components/ResultPanel';
import { Library } from './components/Library';
import { Header } from './components/layout/Header';
import { UrlInput } from './components/forms/UrlInput';
import { LanguageToggle } from './components/forms/LanguageToggle';
import { ErrorDisplay } from './components/ui/ErrorDisplay';

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

    const handleAuthSuccess = useCallback((user: any) => {
        setAuth({ isAuthenticated: true, user });
        setModal('none');
    }, []);

    const handleLogout = useCallback(async () => {
        // Clear the authentication token
        await logoutUser();

        // Clear local state
        setAuth({ isAuthenticated: false, user: null });
        setResult(null);
        setUrl('');
        setView('home'); // Go home on logout
    }, []);

    const handleExtract = useCallback(async () => {
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
    }, [auth.isAuthenticated, url, size, language]);

    return (
        <div className="min-h-screen bg-[#f3f4f6] text-black overflow-x-hidden font-terminal relative">

            {/* Background Halftone Noise */}
            <div className="fixed inset-0 pointer-events-none bg-comic-noise opacity-30 z-0"></div>

            {/* Header / Nav */}
            <Header 
                auth={auth} 
                view={view} 
                setView={setView} 
                handleLogout={handleLogout} 
                setModal={setModal} 
            />

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
                            <UrlInput url={url} setUrl={setUrl}>
                                <LanguageToggle language={language} setLanguage={setLanguage} />
                            </UrlInput>

                            {/* Slider */}
                            <AmpSlider value={size} onChange={setSize} disabled={isLoading} />

                            {/* Error Display */}
                            <ErrorDisplay error={error || ''} />

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