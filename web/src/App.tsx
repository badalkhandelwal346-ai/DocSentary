import React, { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { LandingPage } from "./components/LandingPage";
import { LoginPage } from "./components/LoginPage";
import { SignupPage } from "./components/SignupPage";
import { OnboardingView } from "./components/OnboardingView";
import { Sidebar } from "./components/Sidebar";
import { DashboardView } from "./components/DashboardView";
import { PRAnalysisView } from "./components/PRAnalysisView";
import { RepositoryDetailView } from "./components/RepositoryDetailView";
import { AnalysisHistoryView } from "./components/AnalysisHistoryView";
import { BenchmarkView } from "./components/BenchmarkView";
import { SettingsView } from "./components/SettingsView";
import { AuthModal } from "./components/AuthModal";
import { ExternalLink, User, Compass, LogOut } from "lucide-react";

type ViewRoute = "landing" | "login" | "signup" | "onboarding" | "app";

const MainApp: React.FC = () => {
  const [route, setRoute] = useState<ViewRoute>("landing");
  const [currentTab, setCurrentTab] = useState<string>("dashboard");
  const [selectedRepoId, setSelectedRepoId] = useState<string | undefined>(undefined);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const { user, logout } = useAuth();

  // If user logs in and hasn't finished onboarding, direct them to onboarding if coming from login/signup
  const handleAuthSuccess = () => {
    if (user && !user.onboarding_completed) {
      setRoute("onboarding");
    } else {
      setRoute("app");
    }
  };

  const handleNavigateTab = (tab: string, contextId?: string) => {
    setCurrentTab(tab);
    if (contextId) {
      setSelectedRepoId(contextId);
    }
  };

  if (route === "landing") {
    return (
      <LandingPage
        onNavigateLogin={() => setRoute("login")}
        onNavigateSignup={() => setRoute("signup")}
        onEnterDashboard={() => setRoute("app")}
      />
    );
  }

  if (route === "login") {
    return (
      <LoginPage
        onNavigateSignup={() => setRoute("signup")}
        onNavigateHome={() => setRoute("landing")}
        onLoginSuccess={handleAuthSuccess}
      />
    );
  }

  if (route === "signup") {
    return (
      <SignupPage
        onNavigateLogin={() => setRoute("login")}
        onNavigateHome={() => setRoute("landing")}
        onSignupSuccess={handleAuthSuccess}
      />
    );
  }

  if (route === "onboarding") {
    return (
      <OnboardingView
        onComplete={() => setRoute("app")}
        onNavigateHome={() => setRoute("landing")}
      />
    );
  }

  return (
    <div className="flex h-screen bg-[#F4EFE6] text-[#08161B] font-sans overflow-hidden paper-grain selection:bg-[#1C354D] selection:text-[#EAE7DC]">
      {/* Persistent Left Sidebar */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        onOpenLanding={() => setRoute("landing")}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onOpenOnboarding={() => setRoute("onboarding")}
      />

      {/* Main Workspace Area */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top App Bar */}
        <header className="h-14 border-b border-[#D8CEBC] bg-[#F4EFE6]/90 backdrop-blur px-6 flex items-center justify-between flex-shrink-0 select-none">
          <div className="flex items-center space-x-3 text-xs font-mono text-[#6A7E85]">
            <span className="text-[#08161B] font-bold">DocSentry</span>
            <span>/</span>
            <span className="text-[#1C354D] font-bold uppercase">{currentTab}</span>
            {user?.organization && (
              <>
                <span>/</span>
                <span className="text-[#3D4F55]">{user.organization.name}</span>
              </>
            )}
          </div>

          <div className="flex items-center space-x-3 font-mono text-xs">
            <button
              onClick={() => setRoute("onboarding")}
              className="px-2.5 py-1 rounded bg-[#EBE4D8] hover:bg-[#E2DACB] border border-[#D8CEBC] text-[#3D4F55] hover:text-[#08161B] transition-colors flex items-center space-x-1"
            >
              <Compass className="w-3.5 h-3.5 text-[#C87D55]" />
              <span>Wizard</span>
            </button>

            <button
              onClick={() => setRoute("landing")}
              className="text-[#6A7E85] hover:text-[#08161B] transition-colors hidden sm:inline"
            >
              Public Website
            </button>

            <button
              onClick={() => setIsAuthModalOpen(true)}
              className="px-2.5 py-1 rounded bg-[#EBE4D8] hover:bg-[#E2DACB] text-[#08161B] border border-[#D8CEBC] transition-colors flex items-center space-x-1.5"
            >
              <User className="w-3 h-3 text-[#1C354D]" />
              <span>{user ? user.username : "Sign In"}</span>
            </button>

            {user && (
              <button
                onClick={logout}
                className="p-1.5 text-[#6A7E85] hover:text-[#08161B] transition-colors"
                title="Sign out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            )}

            <a
              href="https://github.com/Atharv386/DocSentary"
              target="_blank"
              rel="noreferrer"
              className="px-2.5 py-1 rounded bg-[#EBE4D8] hover:bg-[#E2DACB] text-[#08161B] border border-[#D8CEBC] transition-colors flex items-center space-x-1"
            >
              <span>GitHub</span>
              <ExternalLink className="w-3 h-3 text-[#6A7E85]" />
            </a>
          </div>
        </header>

        {/* Tab Views */}
        {currentTab === "dashboard" && (
          <DashboardView
            onNavigateTab={handleNavigateTab}
            onOpenOnboarding={() => setRoute("onboarding")}
          />
        )}
        {currentTab === "pr" && <PRAnalysisView selectedRepoId={selectedRepoId} />}
        {currentTab === "repos" && (
          <RepositoryDetailView
            repositoryId={selectedRepoId}
            onBack={() => setCurrentTab("dashboard")}
            onInspectPR={() => setCurrentTab("pr")}
          />
        )}
        {currentTab === "history" && <AnalysisHistoryView />}
        {currentTab === "evaluations" && <BenchmarkView />}
        {currentTab === "settings" && <SettingsView />}
      </main>

      {/* Auth Modal */}
      <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
};
