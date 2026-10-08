import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'

export default function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const userType = localStorage.getItem('userType') || 'candidate'

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userType')
    navigate('/login')
  }

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <Link to="/dashboard" className="text-2xl font-bold text-brand-600">Job Portal</Link>

          <nav className="flex gap-6 items-center">
            <Link
              to="/dashboard"
              className={`${isActive('/dashboard') ? 'text-brand-600 font-medium' : 'text-gray-600'} hover:text-brand-600`}
            >
              Dashboard
            </Link>

            {userType === 'employer' ? (
              <>
                <Link
                  to="/candidates"
                  className={`${isActive('/candidates') ? 'text-brand-600 font-medium' : 'text-gray-600'} hover:text-brand-600`}
                >
                  Search Candidates
                </Link>
                <Link
                  to="/invites"
                  className={`${isActive('/invites') ? 'text-brand-600 font-medium' : 'text-gray-600'} hover:text-brand-600`}
                >
                  Sent Invites
                </Link>
              </>
            ) : (
              <Link
                to="/invites-received"
                className={`${isActive('/invites-received') ? 'text-brand-600 font-medium' : 'text-gray-600'} hover:text-brand-600`}
              >
                Invites Received
              </Link>
            )}

            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-brand-600 text-white rounded hover:bg-brand-700"
            >
              Logout
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
