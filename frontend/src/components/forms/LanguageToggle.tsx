import React from 'react';
import { Language } from '../../types';

interface LanguageToggleProps {
    language: Language;
    setLanguage: (lang: Language) => void;
}

export const LanguageToggle: React.FC<LanguageToggleProps> = ({ language, setLanguage }) => {
    return (
        <div className="flex brutalist-border brutalist-shadow bg-white transform -rotate-2">
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
    );
};
