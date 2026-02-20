import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";
import Layout from "./components/Layout";
import DashboardPage from "./pages/DashboardPage";
import JobDetailPage from "./pages/JobDetailPage";
import ComparePage from "./pages/ComparePage";
import ComparisonDetailPage from "./pages/ComparisonDetailPage";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/jobs/:id" element={<JobDetailPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/compare/:id" element={<ComparisonDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>
);
