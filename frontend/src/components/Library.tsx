import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { LibraryItem, SummarySize, LibraryEntry } from '../types';
import { getLibrary, deleteSummary } from '../services/api';
import { Mascot } from './Mascot';
import { ResultPanel } from './ResultPanel';
import { LoadingSpinner } from './ui/LoadingSpinner';
import { LibraryList } from './library/LibraryList';
import { ErrorDisplay } from './ui/ErrorDisplay';

import mascotStandsWithNotebook from '../pics/mascot_stands_with_a_notebook.png';
import mascotLiesDown from '../pics/mascot_lies_down.png';

// Helper to determine button color based on Size
const getButtonColor = (size: SummarySize): string => {
    switch (size) {
        case SummarySize.SHORT: return 'bg-green-400';
        case SummarySize.MEDIUM: return 'bg-yellow-400';
        case SummarySize.LONG: return 'bg-purple-400 text-white';
    }
};

// Size order for sorting
const SIZE_ORDER: Record<SummarySize, number> = {
    [SummarySize.SHORT]: 1,
    [SummarySize.MEDIUM]: 2,
    [SummarySize.LONG]: 3,
};

export const LibraryComponent: React.FC = () => {
    const [items, setItems] = useState<LibraryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const isMounted = React.useRef(false);

    // State for viewing a specific summary modal
    const [selectedSummary, setSelectedSummary] = useState<{ item: LibraryItem, entry: LibraryEntry } | null>(null);

    useEffect(() => {
        if (isMounted.current) return;
        isMounted.current = true;
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

    const toggleExpand = useCallback((id: string) => {
        setExpandedId(prev => prev === id ? null : id);
    }, []);

    const handleViewSummary = useCallback((e: React.MouseEvent, item: LibraryItem, entry: LibraryEntry) => {
        e.stopPropagation(); // Prevent toggling the accordion
        setSelectedSummary({ item, entry });
    }, []);

    const handleDelete = useCallback(async () => {
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
    }, [selectedSummary]);

    // Memoized sorted entries for each item
    const getSortedEntries = useCallback((entries: LibraryEntry[]) => {
        return [...entries].sort((a, b) => SIZE_ORDER[a.size] - SIZE_ORDER[b.size]);
    }, []);

    return (
        // LAYOUT STRATEGY: 
        // On Mobile: Standard vertical flow, page scrolls normally.
        // On Desktop: Fixed height (viewport minus header), overflow hidden on body, scroll inside left column.
        <div className="container mx-auto px-4 md:px-8 flex flex-col md:flex-row gap-8 md:h-[calc(100vh-120px)] md:overflow-hidden">

            {/* LEFT COLUMN: SCROLLABLE LIST */}
            <div className="w-full md:w-1/2 py-8 order-2 md:order-1 flex flex-col md:h-full">

                {/* Header - Fixed in place (outside scroll container) */}
                <div className="mb-6 flex-shrink-0 self-start">
                    <div className="bg-black text-white p-4 font-marker text-2xl brutalist-transform border-4 border-yellow-400 inline-block shadow-[8px_8px_0px_0px_rgba(76,29,149,1)]">
                        SAVED DATA [{items.length}]
                    </div>
                </div>

                {/* Error Message */}
                <ErrorDisplay error={error || ''} />

                {/* Scrollable List Container - Takes remaining space */}
                <div className="flex-1 w-full md:overflow-y-auto md:pr-4 custom-scrollbar">
                    {loading ? (
                        <div className="flex justify-center items-center py-20">
                            <LoadingSpinner size="lg" />
                        </div>
                    ) : (
                        <LibraryList 
                            items={items}
                            expandedId={expandedId}
                            toggleExpand={toggleExpand}
                            handleViewSummary={handleViewSummary}
                            getSortedEntries={getSortedEntries}
                            getButtonColor={getButtonColor}
                        />
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

// Memoized version for performance optimization
export const Library = React.memo(LibraryComponent);
