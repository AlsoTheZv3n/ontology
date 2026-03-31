import { NavLink, Outlet } from "react-router-dom";

const NAV_CORE = [
  { to: "/", icon: "dashboard", label: "Dashboard" },
  { to: "/feed", icon: "rss_feed", label: "Feed" },
  { to: "/graph", icon: "workspaces", label: "Graph" },
  { to: "/search", icon: "search", label: "Search" },
  { to: "/chat", icon: "smart_toy", label: "Agent" },
];

const NAV_DATA = [
  { to: "/markets", icon: "candlestick_chart", label: "Markets" },
  { to: "/entities", icon: "category", label: "Entities" },
  { to: "/schema", icon: "schema", label: "Schema" },
  { to: "/alerts", icon: "notifications_active", label: "Alerts" },
];

export function Layout() {
  return (
    <div className="flex min-h-screen selection:bg-primary/30">
      {/* Sidebar */}
      <aside className="h-screen w-64 fixed left-0 top-0 bg-surface-container flex flex-col z-50">
        <div className="p-6 mb-4">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-8 h-8 bg-primary rounded-sm flex items-center justify-center">
              <span className="material-symbols-outlined text-surface font-bold">
                radar
              </span>
            </div>
            <div>
              <h1 className="font-headline font-bold text-on-surface text-lg leading-none tracking-tight">
                Sovereign
              </h1>
              <p className="font-label font-medium text-[10px] uppercase tracking-widest text-secondary mt-1">
                Intelligence Engine
              </p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 overflow-y-auto">
          <div className="space-y-0.5">
            {NAV_CORE.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-2.5 font-label font-medium text-xs uppercase tracking-widest transition-all ${
                    isActive
                      ? "bg-surface-container-high text-primary translate-x-1"
                      : "text-secondary hover:bg-surface-container-high/50 hover:text-on-surface"
                  }`
                }
              >
                <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </div>

          <div className="mt-4 mb-1 px-4">
            <span className="text-[9px] text-secondary/40 uppercase tracking-[0.2em] font-label">
              Data
            </span>
          </div>
          <div className="space-y-0.5">
            {NAV_DATA.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-2.5 font-label font-medium text-xs uppercase tracking-widest transition-all ${
                    isActive
                      ? "bg-surface-container-high text-primary translate-x-1"
                      : "text-secondary hover:bg-surface-container-high/50 hover:text-on-surface"
                  }`
                }
              >
                <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>

        <div className="p-3 space-y-1">
          <div className="px-4 py-2 text-[9px] text-secondary/50 uppercase tracking-widest font-label">
            v1.0.0
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="ml-64 flex-1 bg-surface p-12 lg:p-20 max-w-7xl relative technical-grid">
        <Outlet />
      </main>
    </div>
  );
}
