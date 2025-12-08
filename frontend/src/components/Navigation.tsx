import { Link, useLocation } from 'react-router-dom';

function Navigation() {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <nav className="bg-dark-800 border-b border-dark-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link
              to="/"
              className="text-xl font-bold text-blue-400 hover:text-blue-300 transition-colors"
            >
              SectorView
            </Link>
            <div className="flex space-x-4">
              <Link
                to="/"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive('/')
                    ? 'bg-blue-600 text-white'
                    : 'text-dark-300 hover:bg-dark-700 hover:text-dark-100'
                }`}
              >
                Dashboard
              </Link>
              <Link
                to="/sector-rotation"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive('/sector-rotation')
                    ? 'bg-blue-600 text-white'
                    : 'text-dark-300 hover:bg-dark-700 hover:text-dark-100'
                }`}
              >
                Sector Rotation
              </Link>
              <Link
                to="/stock-screener"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive('/stock-screener')
                    ? 'bg-blue-600 text-white'
                    : 'text-dark-300 hover:bg-dark-700 hover:text-dark-100'
                }`}
              >
                Stock Screener
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navigation;

