import { Route, Routes } from "react-router-dom";

import { Navbar } from "./components/Navbar";
import { RequireAuth } from "./components/RequireAuth";
import { Cart } from "./pages/Cart";
import { Catalog } from "./pages/Catalog";
import { Checkout } from "./pages/Checkout";
import { Dashboard } from "./pages/Dashboard";
import { Login } from "./pages/Login";
import { Profile } from "./pages/Profile";
import { Register } from "./pages/Register";

export function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/catalog" element={<Catalog />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/cart" element={<RequireAuth><Cart /></RequireAuth>} />
        <Route path="/checkout" element={<RequireAuth><Checkout /></RequireAuth>} />
        <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
      </Routes>
    </>
  );
}
