import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Overview } from './pages/Overview';
import { SessionReplay } from './pages/SessionReplay';
import { TraderBaseline } from './pages/TraderBaseline';
import { InterventionHistory } from './pages/InterventionHistory';
import { Evaluation } from './pages/Evaluation';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="replay" element={<SessionReplay />} />
          <Route path="baseline" element={<TraderBaseline />} />
          <Route path="interventions" element={<InterventionHistory />} />
          <Route path="evaluation" element={<Evaluation />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
