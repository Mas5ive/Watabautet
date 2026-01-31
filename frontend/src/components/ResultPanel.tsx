import React, { useState } from 'react';
import { SummaryResult } from '../types';
import { mockSaveToLibrary } from '../services/mockBackend';
import { Save, XCircle, Terminal, Trash2 } from 'lucide-react';

interface ResultPanelProps {
  result: SummaryResult;
  onClose: () => void;
  mode?: 'preview' | 'view'; // preview = extract page, view = library page
  onDelete?: () => void;
}

export const ResultPanel: React.FC<ResultPanelProps> = ({ result, onClose, mode = 'preview', onDelete }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setIsProcessing(true);
    await mockSaveToLibrary(result);
    setSaved(true);
    setIsProcessing(false);
  };

  const handleDelete = async () => {
    if (onDelete) {
      setIsProcessing(true);
      await onDelete();
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="bg-white border-4 border-black shadow-[16px_16px_0px_0px_rgba(250,204,21,1)] w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col relative transform rotate-1">

        {/* Header - Terminal Style */}
        <div className="bg-black text-white p-4 flex justify-between items-center font-terminal text-xl border-b-4 border-black">
          <div className="flex items-center gap-2">
            <Terminal size={24} className="text-yellow-400" />
            <span className="uppercase tracking-widest">WATABAUTET-OS v.2.0.84 // {mode === 'view' ? 'ARCHIVE' : 'OUTPUT'}</span>
          </div>
          <button onClick={onClose} className="hover:text-yellow-400 transition-colors">
            <XCircle size={32} />
          </button>
        </div>

        {/* Content */}
        <div className="p-8 overflow-y-auto bg-comic-noise flex-1">
          <h2 className="font-marker text-3xl mb-6 text-purple-900 border-b-4 border-black pb-2 leading-tight">
            {result.title}
          </h2>

          <div className="space-y-4 font-terminal text-2xl leading-relaxed text-gray-900">
            {result.content.map((paragraph, idx) => (
              <p key={idx} className="bg-white/80 p-2 border border-dashed border-gray-400 shadow-sm">
                <span className="text-purple-800 font-bold mr-2">{`>`}</span>
                {paragraph}
              </p>
            ))}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-6 bg-white border-t-4 border-black flex justify-between items-center">
          <div className="font-marker text-xl text-gray-500 rotate-2 flex items-center gap-2">
            <span>MODE: {result.size}</span>
            <span className="bg-black text-white px-1 text-sm">{result.language}</span>
          </div>

          {mode === 'preview' ? (
            <button
              onClick={handleSave}
              disabled={saved || isProcessing}
              className={`
                        flex items-center gap-2 px-6 py-3 border-4 border-black font-bold font-terminal text-xl
                        transition-all duration-200
                        ${saved
                  ? 'bg-green-400 text-black cursor-default'
                  : 'bg-white hover:bg-black hover:text-white active:translate-y-1'
                }
                        shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]
                    `}
            >
              {saved ? (
                <>SAVED TO ARCHIVE</>
              ) : (
                <>
                  <Save size={20} />
                  {isProcessing ? 'UPLOADING...' : 'SAVE TO LIBRARY'}
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleDelete}
              disabled={isProcessing}
              className="
                        flex items-center gap-2 px-6 py-3 border-4 border-black font-bold font-terminal text-xl
                        transition-all duration-200
                        bg-red-500 text-white hover:bg-red-700 hover:shadow-none active:translate-y-1
                        shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]
                    "
            >
              <Trash2 size={20} />
              {isProcessing ? 'DELETING...' : 'DELETE ENTRY'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};