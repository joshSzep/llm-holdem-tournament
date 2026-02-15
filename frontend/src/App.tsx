import { BrowserRouter, Routes, Route } from "react-router-dom";

import { Lobby } from "./pages/Lobby/Lobby";
import { GameTable } from "./pages/GameTable/GameTable";
import { PostGame } from "./pages/PostGame/PostGame";
import { GameReview } from "./pages/GameReview/GameReview";

function App(): React.ReactElement {
  return (
    <BrowserRouter>
      <div className="app">
        <Routes>
          <Route path="/" element={<Lobby />} />
          <Route path="/game/:id" element={<GameTable />} />
          <Route path="/game/:id/results" element={<PostGame />} />
          <Route path="/game/:id/review" element={<GameReview />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
