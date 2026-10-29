import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AnalysisPage } from "./pages/AnalysisPage";
import { LandingPage } from "./pages/LandingPage";
import { UploadPage } from "./pages/UploadPage";
import { OptimizationPage } from "./pages/OptimizationPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/analyze" element={<UploadPage />} />
        <Route path="/analysis/:id" element={<AnalysisPage />} />
        <Route path="/analysis/:id/optimize" element={<OptimizationPage />} />
      </Routes>
    </Layout>
  );
}
