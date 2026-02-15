import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";

import { Lobby } from "./pages/Lobby/Lobby";
import { GameTable } from "./pages/GameTable/GameTable";
import { PostGame } from "./pages/PostGame/PostGame";
import { GameReview } from "./pages/GameReview/GameReview";
import { PageTransition } from "./components/transitions/PageTransition";

function AnimatedRoutes(): React.ReactElement {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route
          path="/"
          element={
            <PageTransition>
              <Lobby />
            </PageTransition>
          }
        />
        <Route
          path="/game/:id"
          element={
            <PageTransition variant="slide">
              <GameTable />
            </PageTransition>
          }
        />
        <Route
          path="/game/:id/results"
          element={
            <PageTransition>
              <PostGame />
            </PageTransition>
          }
        />
        <Route
          path="/game/:id/review"
          element={
            <PageTransition variant="slide">
              <GameReview />
            </PageTransition>
          }
        />
      </Routes>
    </AnimatePresence>
  );
}

function App(): React.ReactElement {
  return (
    <BrowserRouter>
      <div className="app">
        <AnimatedRoutes />
      </div>
    </BrowserRouter>
  );
}

export default App;
