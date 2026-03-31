import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "./index.css";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Graph } from "./pages/Graph";
import { Company } from "./pages/Company";
import { Search } from "./pages/Search";
import { Chat } from "./pages/Chat";
import { Feed } from "./pages/Feed";
import { Markets } from "./pages/Markets";
import { Entities } from "./pages/Entities";
import { Schema } from "./pages/Schema";
import { Alerts } from "./pages/Alerts";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/graph" element={<Graph />} />
            <Route path="/graph/:rootKey" element={<Graph />} />
            <Route path="/company/:key" element={<Company />} />
            <Route path="/search" element={<Search />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/feed" element={<Feed />} />
            <Route path="/markets" element={<Markets />} />
            <Route path="/entities" element={<Entities />} />
            <Route path="/schema" element={<Schema />} />
            <Route path="/alerts" element={<Alerts />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
