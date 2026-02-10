import React from 'react';

interface UrlInputProps {
    url: string;
    setUrl: (url: string) => void;
    label?: string;
    children?: React.ReactNode;
}

export const UrlInput: React.FC<UrlInputProps> = ({ 
    url, 
    setUrl, 
    label = "YOUTUBE VIDEO",
    children 
}) => {
    return (
        <div className="mb-8">
            <div className="flex justify-between items-end mb-2">
                <label className="font-marker text-2xl transform -skew-x-6 inline-block bg-black text-white px-2">
                    {label}
                </label>
                {children}
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
    );
};
