import { Link, NavLink, Outlet } from "react-router-dom";

export default function Layout() {
  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-8">
          <Link to="/" className="text-xl font-bold text-gray-900">
            Queued Agents
          </Link>
          <nav className="flex gap-4 text-sm">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                isActive ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-700"
              }
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/prompts"
              className={({ isActive }) =>
                isActive ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-700"
              }
            >
              Prompts
            </NavLink>
            <NavLink
              to="/compare"
              className={({ isActive }) =>
                isActive ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-700"
              }
            >
              Compare
            </NavLink>
            <NavLink
              to="/leaderboard"
              className={({ isActive }) =>
                isActive ? "text-blue-600 font-medium" : "text-gray-500 hover:text-gray-700"
              }
            >
              Leaderboard
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
