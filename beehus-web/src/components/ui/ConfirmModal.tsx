

interface ConfirmModalProps {
    isOpen: boolean;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    isDanger?: boolean;
    onConfirm: () => void;
    onCancel: () => void;
}

export default function ConfirmModal({
    isOpen,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    isDanger = false,
    onConfirm,
    onCancel
}: ConfirmModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[70] p-4 animate-in fade-in duration-200">
            <div className="glass p-6 rounded-xl border border-white/10 w-full max-w-sm shadow-2xl scale-100 animate-in zoom-in-95 duration-200 transform transition-all">
                <h3 className="text-xl font-bold text-white mb-2">{title}</h3>
                <p className="text-slate-300 mb-6 text-sm leading-relaxed">{message}</p>
                
                <div className="flex space-x-3">
                    <button
                        onClick={onCancel}
                        className="flex-1 bg-white/5 hover:bg-white/10 text-white px-4 py-2.5 rounded-lg font-medium transition-colors border border-white/5"
                    >
                        {cancelText}
                    </button>
                    <button
                        onClick={onConfirm}
                        className={`flex-1 px-4 py-2.5 rounded-lg font-medium shadow-lg transition-all ${
                            isDanger 
                                ? 'bg-red-600 hover:bg-red-500 text-white shadow-red-500/20 border border-red-500/30' 
                                : 'bg-brand-600 hover:bg-brand-500 text-white shadow-brand-500/20 border border-brand-500/30'
                        }`}
                    >
                        {confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
}
