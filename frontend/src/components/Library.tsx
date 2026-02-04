import React, { useEffect, useState } from 'react';
import { LibraryItem, SummarySize, LibraryEntry } from '../types';
import { getLibrary, deleteSummary } from '../services/api';
import { Mascot } from './Mascot';
import { ResultPanel } from './ResultPanel';
import { ChevronDown, ChevronUp, Loader2, PlayCircle } from 'lucide-react';

import mascotStandsWithNotebook from '../pics/mascot_stands_with_a_notebook.png';
import mascotLiesDown from '../pics/mascot_lies_down.png';

export const Library: React.FC = () => {
    const [items, setItems] = useState<LibraryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // State for viewing a specific summary modal
    const [selectedSummary, setSelectedSummary] = useState<{ item: LibraryItem, entry: LibraryEntry } | null>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getLibrary();
            setItems(data);
        } catch (e: any) {
            setError(e.message || 'Failed to load library');
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const toggleExpand = (id: string) => {
        setExpandedId(prev => prev === id ? null : id);
    };

    const handleViewSummary = (e: React.MouseEvent, item: LibraryItem, entry: LibraryEntry) => {
        e.stopPropagation(); // Prevent toggling the accordion
        setSelectedSummary({ item, entry });
    };

    const handleDelete = async () => {
        if (!selectedSummary) return;

        try {
            await deleteSummary(selectedSummary.item.videoId, selectedSummary.entry.size, selectedSummary.entry.language);
            // Update local state to remove item
            setItems(prev => prev.filter(i => i.id !== selectedSummary.item.id));
            // Close modal
            setSelectedSummary(null);
        } catch (e: any) {
            setError(e.message || 'Failed to delete summary');
        }
    };

    // Helper to determine button color based on Size
    const getButtonColor = (size: SummarySize) => {
        switch (size) {
            case SummarySize.SHORT: return 'bg-green-400';
            case SummarySize.MEDIUM: return 'bg-yellow-400';
            case SummarySize.LONG: return 'bg-purple-400 text-white';
        }
    };

    return (
        // LAYOUT STRATEGY: 
        // On Mobile: Standard vertical flow, page scrolls normally.
        // On Desktop: Fixed height (viewport minus header), overflow hidden on body, scroll inside left column.
        <div className="container mx-auto px-4 md:px-8 flex flex-col md:flex-row gap-8 md:h-[calc(100vh-120px)] md:overflow-hidden">

            {/* LEFT COLUMN: SCROLLABLE LIST */}
            <div className="w-full md:w-1/2 py-8 order-2 md:order-1 flex flex-col md:h-full">

                {/* Header - Fixed in place (outside scroll container) */}
                <div className="mb-6 flex-shrink-0 self-start">
                    <div className="bg-black text-white p-4 font-marker text-2xl transform -rotate-1 border-4 border-yellow-400 inline-block shadow-[8px_8px_0px_0px_rgba(76,29,149,1)]">
                        SAVED DATA [{items.length}]
                    </div>
                </div>

                {/* Error Message */}
                {error && (
                    <div className="mb-4 p-4 bg-red-100 border-4 border-red-500 text-red-700 font-terminal text-lg">
                        ERROR: {error}
                    </div>
                )}

                {/* Scrollable List Container - Takes remaining space */}
                <div className="flex-1 w-full md:overflow-y-auto md:pr-4 custom-scrollbar">
                    {loading ? (
                        <div className="flex justify-center items-center py-20">
                            <Loader2 className="animate-spin w-16 h-16 text-black" />
                        </div>
                    ) : (
                        <div className="space-y-4 pb-20 md:pb-0">
                            {items.map((item) => {
                                const isExpanded = expandedId === item.id;

                                // Sort entries to be neat: Short -> Medium -> Long
                                const sortedEntries = [...item.entries].sort((a, b) => {
                                    const order = { [SummarySize.SHORT]: 1, [SummarySize.MEDIUM]: 2, [SummarySize.LONG]: 3 };
                                    return order[a.size] - order[b.size];
                                });

                                return (
                                    <div
                                        key={item.id}
                                        onClick={() => toggleExpand(item.id)}
                                        className={`
                                    relative border-4 border-black bg-white transition-all duration-200 cursor-pointer
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
                            })}
                        </div>
                    )}
                </div>
            </div>

            {/* RIGHT COLUMN: STATIC MASCOT */}
            <div className="w-full md:w-1/2 order-1 md:order-2 md:h-full flex items-end justify-center md:justify-end md:pb-4 overflow-hidden">
                <Mascot
                    desktopSrc={mascotStandsWithNotebook}
                    mobileSrc={mascotLiesDown}
                />
            </div>

            {/* MODAL */}
            {selectedSummary && (
                <ResultPanel
                    result={{
                        title: selectedSummary.item.title,
                        size: selectedSummary.entry.size,
                        content: selectedSummary.entry.content,
                        language: selectedSummary.entry.language
                    }}
                    mode="view"
                    onClose={() => setSelectedSummary(null)}
                    onDelete={handleDelete}
                />
            )}
        </div>
    );
};