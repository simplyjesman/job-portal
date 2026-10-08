import { useState } from 'react'

export default function CandidateSearchPage() {
  const [location, setLocation] = useState('')

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Search Candidates</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Filters */}
        <div className="md:col-span-1">
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g., London, UK"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Skills</label>
              <input
                type="text"
                placeholder="Search skills..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <button className="w-full bg-brand-600 text-white py-2 rounded-md hover:bg-brand-700">
              Filter
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="md:col-span-3">
          <div className="space-y-4">
            <p className="text-gray-500 text-center py-12">No candidates found</p>
          </div>
        </div>
      </div>
    </div>
  )
}
