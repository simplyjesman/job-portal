import { useState } from 'react'
import api from '../services/api'

interface Candidate {
  id: number
  email: string
  first_name: string
  last_name: string
  location: string
  skills: string[]
  salary_expectations: number
  availability: string
}

interface InviteForm {
  job_title: string
  job_description: string
  salary_min: number
  salary_max: number
  location: string
  message: string
}

export default function CandidateSearchPage() {
  const [location, setLocation] = useState('')
  const [skills, setSkills] = useState('')
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedCandidate, setSelectedCandidate] = useState<number | null>(null)
  const [showInviteForm, setShowInviteForm] = useState(false)
  const [inviteForm, setInviteForm] = useState<InviteForm>({
    job_title: '',
    job_description: '',
    salary_min: 0,
    salary_max: 0,
    location: '',
    message: '',
  })
  const [sendingInvite, setSendingInvite] = useState(false)

  const handleSearch = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (location) params.append('location', location)
      if (skills) params.append('skills', skills)

      const response = await api.get(`/employer/candidates/?${params}`)
      setCandidates(response.data)
    } catch (error) {
      console.error('Failed to search candidates:', error)
      alert('Failed to search candidates')
    } finally {
      setLoading(false)
    }
  }

  const handleSendInvite = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCandidate) return

    setSendingInvite(true)
    try {
      await api.post('/employer/invites/send_invite/', {
        candidate_id: selectedCandidate,
        ...inviteForm,
      })
      alert('Interview invite sent!')
      setShowInviteForm(false)
      setInviteForm({ job_title: '', job_description: '', salary_min: 0, salary_max: 0, location: '', message: '' })
      setSelectedCandidate(null)
    } catch (error) {
      console.error('Failed to send invite:', error)
      alert('Failed to send invite')
    } finally {
      setSendingInvite(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Search & Invite Candidates</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Filters */}
        <div className="md:col-span-1">
          <div className="bg-white rounded-lg shadow p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Filters</h2>

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
                value={skills}
                onChange={(e) => setSkills(e.target.value)}
                placeholder="e.g., Python, Django"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>

            <button
              onClick={handleSearch}
              disabled={loading}
              className="w-full bg-brand-600 text-white py-2 rounded-md hover:bg-brand-700 disabled:bg-gray-400"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="md:col-span-3">
          {candidates.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
              <p>No candidates found. Try searching with different filters.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {candidates.map((candidate) => (
                <div key={candidate.id} className="bg-white rounded-lg shadow p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {candidate.first_name} {candidate.last_name}
                      </h3>
                      <p className="text-sm text-gray-500">{candidate.email}</p>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedCandidate(candidate.id)
                        setShowInviteForm(true)
                        setInviteForm({ ...inviteForm, location: candidate.location })
                      }}
                      className="px-4 py-2 bg-brand-600 text-white rounded hover:bg-brand-700"
                    >
                      Send Invite
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">Location</p>
                      <p className="font-medium text-gray-900">{candidate.location}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Salary Expectations</p>
                      <p className="font-medium text-gray-900">£{candidate.salary_expectations?.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Availability</p>
                      <p className="font-medium text-gray-900 capitalize">{candidate.availability?.replace('_', ' ')}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Skills</p>
                      <p className="font-medium text-gray-900">{candidate.skills?.join(', ') || 'N/A'}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Invite Form Modal */}
      {showInviteForm && selectedCandidate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 space-y-4">
              <h2 className="text-2xl font-bold text-gray-900">Send Interview Invite</h2>

              <form onSubmit={handleSendInvite} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
                  <input
                    type="text"
                    placeholder="e.g., Senior Python Developer"
                    value={inviteForm.job_title}
                    onChange={(e) => setInviteForm({ ...inviteForm, job_title: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Job Description</label>
                  <textarea
                    placeholder="Describe the role, responsibilities, and requirements..."
                    value={inviteForm.job_description}
                    onChange={(e) => setInviteForm({ ...inviteForm, job_description: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    rows={4}
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Min Salary (£)</label>
                    <input
                      type="number"
                      value={inviteForm.salary_min}
                      onChange={(e) => setInviteForm({ ...inviteForm, salary_min: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max Salary (£)</label>
                    <input
                      type="number"
                      value={inviteForm.salary_max}
                      onChange={(e) => setInviteForm({ ...inviteForm, salary_max: parseInt(e.target.value) })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                  <input
                    type="text"
                    value={inviteForm.location}
                    onChange={(e) => setInviteForm({ ...inviteForm, location: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Message (Optional)</label>
                  <textarea
                    placeholder="Add a personal message for the candidate..."
                    value={inviteForm.message}
                    onChange={(e) => setInviteForm({ ...inviteForm, message: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                    rows={3}
                  />
                </div>

                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => setShowInviteForm(false)}
                    className="px-4 py-2 bg-gray-300 text-gray-900 rounded hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={sendingInvite}
                    className="px-4 py-2 bg-brand-600 text-white rounded hover:bg-brand-700 disabled:bg-gray-400"
                  >
                    {sendingInvite ? 'Sending...' : 'Send Invite'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
