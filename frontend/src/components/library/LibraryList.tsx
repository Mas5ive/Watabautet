import React from 'react';
import { LibraryItem, LibraryEntry, SummarySize } from '../../types';
import { LibraryItemComponent } from './LibraryItem';

interface LibraryListProps {
    items: LibraryItem[];
    expandedId: string | null;
    toggleExpand: (id: string) => void;
    handleViewSummary: (e: React.MouseEvent, item: LibraryItem, entry: LibraryEntry) => void;
    getSortedEntries: (entries: LibraryEntry[]) => LibraryEntry[];
    getButtonColor: (size: SummarySize) => string;
}

export const LibraryList: React.FC<LibraryListProps> = ({
    items,
    expandedId,
    toggleExpand,
    handleViewSummary,
    getSortedEntries,
    getButtonColor
}) => {
    return (
        <div className="space-y-4 pb-20 md:pb-0">
            {items.map((item) => (
                <LibraryItemComponent
                    key={item.id}
                    item={item}
                    isExpanded={expandedId === item.id}
                    toggleExpand={toggleExpand}
                    handleViewSummary={handleViewSummary}
                    sortedEntries={getSortedEntries(item.entries)}
                    getButtonColor={getButtonColor}
                />
            ))}
        </div>
    );
};
