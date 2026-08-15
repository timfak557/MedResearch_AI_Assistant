import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppProvider } from "@/context/AppContext";
import { Layout } from "@/components/layout/Layout";
import { ChatPage } from "@/pages/ChatPage";
import { Skeleton } from "@/components/common/LoadingState";

// Chat is the primary route and loads eagerly; secondary pages are lazy.
const SearchPage = lazy(() => import("@/pages/SearchPage").then((m) => ({ default: m.SearchPage })));
const HistoryPage = lazy(() => import("@/pages/HistoryPage").then((m) => ({ default: m.HistoryPage })));
const SavedSourcesPage = lazy(() => import("@/pages/SavedSourcesPage").then((m) => ({ default: m.SavedSourcesPage })));
const SettingsPage = lazy(() => import("@/pages/SettingsPage").then((m) => ({ default: m.SettingsPage })));
const AboutPage = lazy(() => import("@/pages/AboutPage").then((m) => ({ default: m.AboutPage })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

function PageFallback() {
  return (
    <div className="mx-auto max-w-2xl space-y-3 p-8">
      <Skeleton className="h-8 w-56" />
      <Skeleton className="h-32" />
      <Skeleton className="h-32" />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<ChatPage />} />
              <Route
                path="/search"
                element={<Suspense fallback={<PageFallback />}><SearchPage /></Suspense>}
              />
              <Route
                path="/history"
                element={<Suspense fallback={<PageFallback />}><HistoryPage /></Suspense>}
              />
              <Route
                path="/saved"
                element={<Suspense fallback={<PageFallback />}><SavedSourcesPage /></Suspense>}
              />
              <Route
                path="/settings"
                element={<Suspense fallback={<PageFallback />}><SettingsPage /></Suspense>}
              />
              <Route
                path="/about"
                element={<Suspense fallback={<PageFallback />}><AboutPage /></Suspense>}
              />
            </Route>
          </Routes>
        </BrowserRouter>
      </AppProvider>
    </QueryClientProvider>
  );
}
