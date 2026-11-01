import React, { useState } from "react";
import { Key, AlertCircle, X, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const { user, directLogin, logout } = useAuth();
  const [username, setUsername] = useState("octocat");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDirectLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      await directLogin(username.trim());
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to log in");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 font-sans paper-grain">
      <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg max-w-md w-full p-6 space-y-6 shadow-editorial text-[#08161B]">
        <div className="flex items-center justify-between border-b border-[#D8CEBC] pb-3">
          <div className="flex items-center space-x-2">
            <Key className="w-5 h-5 text-[#1C354D]" />
            <h2 className="font-serif font-bold text-lg text-[#08161B]">Developer Authentication</h2>
          </div>
          <button
            onClick={onClose}
            className="text-[#6A7E85] hover:text-[#08161B] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {user ? (
          <div className="space-y-4">
            <div className="p-4 rounded bg-[#F4EFE6] border border-[#D8CEBC] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#6A7E85] font-mono uppercase">
                  CURRENTLY SIGNED IN
                </span>
                <span className="w-2 h-2 rounded-full bg-[#4A6B32]"></span>
              </div>
              <div className="font-serif font-bold text-lg text-[#08161B]">
                {user.full_name || user.username}
              </div>
              <div className="text-xs text-[#3D4F55] font-mono">Username: @{user.username}</div>
              <div className="text-xs text-[#4A6B32] font-mono">
                Workspace: {user.organization?.name}
              </div>
            </div>

            <button
              onClick={() => {
                logout();
                onClose();
              }}
              className="w-full py-2.5 rounded bg-[#F4EFE6] hover:bg-[#E2DACB] border border-[#D8CEBC] text-xs font-mono text-[#08161B] flex items-center justify-center space-x-2 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out of Session</span>
            </button>
          </div>
        ) : (
          <div className="space-y-4 font-mono text-xs">
            {errorMsg && (
              <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleDirectLogin} className="space-y-3">
              <div className="space-y-1">
                <label className="text-[#3D4F55] block">Developer Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. octocat, admin"
                  className="w-full px-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B] text-xs focus:outline-none focus:border-[#1C354D]"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-semibold text-xs transition-colors shadow-paper"
              >
                <span>{loading ? "Authenticating..." : "Fast-Track Local Developer Sign In"}</span>
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};
