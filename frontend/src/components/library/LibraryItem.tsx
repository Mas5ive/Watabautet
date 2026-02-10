import React from 'react';
import { LibraryItem, LibraryEntry, SummarySize } from '../../types';
import { ChevronDown, ChevronUp, PlayCircle } from 'lucide-react';

interface LibraryItemProps {
    item: LibraryItem;
    isExpanded: boolean;
    toggleExpand: (id: string) => void;
    handleViewSummary: (e: React.MouseEvent, item: LibraryItem, entry: LibraryEntry) => void;
    sortedEntries: LibraryEntry[];
    getButtonColor: (size: SummarySize) => string;
}

export const LibraryItemComponent: React.FC<LibraryItemProps> = ({
    item,
    isExpanded,
    toggleExpand,
    handleViewSummary,
    sortedEntries,
    getButtonColor
}) => {
    return (
        <div
            onClick={() => toggleExpand(item.id)}
            className={`
                relative brutalist-border bg-white transition-all duration-200 cursor-pointer
                ${isExpanded ? 'shadow-[8px_8px_0px_0px_#000] translate-x-1 -translate-y-1' : 'shadow-[4px_4px_0px_0px_#aaa] hover:shadow-[6px_6px_0px_0px_#000]'}
            `}
        >
            {/* Header of the Item */}
            <div className={`p-4 flex justify-between items-center ${isExpanded ? 'bg-yellow-50' : ''}`}>
                <div className="flex-1 pr-4">
                    <h3 className="font-marker text-xl leading-none mb-1">{item.title}</h3>
                    <div className="font-terminal text-gray-500 text-lg flex items-center gap-2">
                        <PlayCircle size={16} /> ID: {item.videoId}
                    </div>
                </div>
                <div>
                    {isExpanded ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
                </div>
            </div>

            {/* Expanded Content (Buttons) */}
            {isExpanded && (
                <div className="border-t-4 border-black p-4 bg-comic-noise flex flex-wrap gap-4 animate-in slide-in-from-top-2 duration-200">
                    <div className="w-full font-terminal text-gray-600 mb-2 uppercase font-bold text-sm tracking-widest">
                        Available Formats ({sortedEntries.length}):
                    </div>

                    {sortedEntries.map((entry, idx) => (
                        <button
                            key={`${item.id}-${idx}`}
                            onClick={(e) => handleViewSummary(e, item, entry)}
                            className={`
                                group
                                relative flex-1 min-w-[150px] py-3 
                                ${getButtonColor(entry.size)} 
                                border-2 border-black 
                                shadow-[3px_3px_0px_0px_#000] hover:translate-y-1 hover:shadow-none 
                                transition-all flex items-center justify-center gap-3
                            `}
                        >
                            {/* LANGUAGE STAMP: Replaces Icon */}
                            <span className="bg-black text-white font-terminal font-bold text-xl px-2 border-2 border-white/20 transform -rotate-3 group-hover:rotate-0 transition-transform duration-200 shadow-sm">
                                {entry.language}
                            </span>

                            {/* SIZE LABEL */}
                            <span className="font-marker text-xl leading-none pt-1">
                                {entry.size}
                            </span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};
