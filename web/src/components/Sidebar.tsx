import React from "react";
import {
  Shield,
  LayoutDashboard,
  GitPullRequest,
  BookOpen,
  History,
  Settings,
  Layers,
  Activity,
  User as UserIcon,
  Compass,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  onOpenLanding: () => void;
  onOpenAuth: () => void;
  onOpenOnboarding: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  onOpenLanding,
  onOpenAuth,
  onOpenOnboarding,
}) => {
  const { user } = useAuth();

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "pr", label: "PR Analysis", icon: GitPullRequest, badge: "Live" },
    { id: "repos", label: "Repositories", icon: BookOpen },
    { id: "history", label: "Scan History", icon: History },
    { id: "evaluations", label: "Evaluations", icon: Activity, badge: "78.1%" },
    { id: "settings", label: "Settings & GitHub", icon: Settings },
  ];

  return (
    <aside className="w-64 border-r border-[#D8CEBC] bg-[#EBE4D8] flex flex-col justify-between h-screen select-none font-sans paper-grain text-[#08161B]">
      <div>
        {/* Brand */}
        <div className="p-5 border-b border-[#D8CEBC] flex items-center justify-between">
          <div className="flex items-center space-x-2.5 cursor-pointer" onClick={onOpenLanding}>
            <div className="w-8 h-8 rounded bg-[#1C354D] text-[#EAE7DC] flex items-center justify-center shadow-paper border border-[#1D5B6B]">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <span className="font-serif text-lg font-bold tracking-tight text-[#08161B] block leading-none">
                DocSentry
              </span>
              <span className="block text-[9px] text-[#6A7E85] font-mono tracking-widest uppercase mt-0.5">
                Reliability Engine
              </span>
            </div>
          </div>
          <span className="text-[10px] font-mono text-[#4A6B32] bg-[#4A6B32]/10 px-2 py-0.5 rounded border border-[#4A6B32]/30 font-bold">
            v0.2
          </span>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-2 text-[10px] font-mono text-[#6A7E85] tracking-widest uppercase">
            Platform Views
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded text-xs font-mono transition-all ${
                  isActive
                    ? "bg-[#F4EFE6] text-[#08161B] border-l-2 border-l-[#C87D55] border-y border-r border-[#D8CEBC] font-bold shadow-sm"
                    : "text-[#3D4F55] hover:text-[#08161B] hover:bg-[#E2DACB]"
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon
                    className={`w-4 h-4 ${isActive ? "text-[#1C354D]" : "text-[#6A7E85]"}`}
                  />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.2 rounded ${
                      isActive
                        ? "bg-[#1C354D] text-[#EAE7DC]"
                        : "bg-[#D8CEBC] text-[#3D4F55]"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Setup Wizard shortcut */}
        <div className="px-3 pt-2">
          <button
            onClick={onOpenOnboarding}
            className="w-full flex items-center justify-between px-3 py-2 rounded bg-[#F4EFE6] border border-[#D8CEBC] text-xs font-mono text-[#3D4F55] hover:text-[#08161B] hover:border-[#1C354D] transition-colors"
          >
            <div className="flex items-center space-x-2">
              <Compass className="w-3.5 h-3.5 text-[#C87D55]" />
              <span>Setup Wizard</span>
            </div>
            <span className="text-[10px] text-[#6A7E85]">7 steps</span>
          </button>
        </div>

        {/* Core Engine Specs quick link */}
        <div className="px-4 py-3 mx-3 my-3 bg-[#F4EFE6] border border-[#D8CEBC] rounded">
          <div className="flex items-center justify-between text-xs font-mono font-bold text-[#08161B] mb-1">
            <span className="flex items-center space-x-1.5">
              <Layers className="w-3.5 h-3.5 text-[#1C354D]" />
              <span>Engine Status</span>
            </span>
            <span className="text-[10px] text-[#4A6B32]">ONLINE</span>
          </div>
          <p className="text-[11px] text-[#6A7E85] leading-tight">
            Deterministic AST + Qwen3-8B dual-span verification.
          </p>
        </div>
      </div>

      {/* User Profile & Footer */}
      <div className="p-3 border-t border-[#D8CEBC] space-y-2">
        <button
          onClick={onOpenAuth}
          className="w-full flex items-center justify-between p-2 rounded bg-[#F4EFE6] hover:bg-[#E2DACB] border border-[#D8CEBC] text-xs transition-colors"
        >
          <div className="flex items-center space-x-2.5 truncate">
            <div className="w-7 h-7 rounded-full bg-[#1C354D] text-[#EAE7DC] flex items-center justify-center font-mono font-bold text-xs">
              {user?.username ? user.username.slice(0, 2).toUpperCase() : <UserIcon className="w-3.5 h-3.5" />}
            </div>
            <div className="text-left truncate">
              <div className="text-[#08161B] font-semibold truncate text-xs">
                {user?.full_name || user?.username || "Sign In"}
              </div>
              <div className="text-[10px] text-[#6A7E85] truncate font-mono">
                {user?.organization?.name || "Developer Profile"}
              </div>
            </div>
          </div>
          <span className="text-[10px] font-mono text-[#4A6B32] font-semibold">
            {user ? "Active" : "Login"}
          </span>
        </button>

        <div className="flex items-center justify-between px-1 text-[10px] text-[#6A7E85] border-t border-[#D8CEBC]/60 pt-2 font-mono">
          <span>DocSentry v0.2</span>
          <span className="flex items-center text-[#4A6B32] space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4A6B32]"></span>
            <span>Live</span>
          </span>
        </div>
      </div>
    </aside>
  );
};
