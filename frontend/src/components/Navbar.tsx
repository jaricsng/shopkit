import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/context";

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const onLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <NavLink to="/" className="brand">ShopKit</NavLink>
      <NavLink to="/catalog">Catalog</NavLink>
      {user && <NavLink to="/cart">Cart</NavLink>}
      <span className="spacer" />
      {user ? (
        <>
          <NavLink to="/profile">{user.display_name || user.full_name || user.email}</NavLink>
          <button className="secondary" onClick={onLogout}>Log out</button>
        </>
      ) : (
        <>
          <NavLink to="/login">Log in</NavLink>
          <NavLink to="/register">Register</NavLink>
        </>
      )}
    </nav>
  );
}
