import { useState, useEffect } from 'react'
import api from '../services/api'

interface InterviewInvite {
  id: number
  job_title: string
  candidate_name: string
  candidate_email: string
  status: 'sent' | 'accepted' | 'declined'
  sent_at: string
  accepted_at?: string
}

export default function JobsPage() {
  const [invites, setInvites] = useState<InterviewInvite[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'sent' | 'accepted' | 'declined'>('all')

  useEffect(() => {
    fetchInvites()
  }, [])

  const fetchInvites = async () => {
    setLoading(true)
    try {
      const response = await api.get('/employer/invites/')
      setInvites(response.data)
    } catch (error) {
      console.error('Failed to fetch invites:', error)
      alert('Failed to load invites')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async (inviteId: number) => {
    if (!confirm('Are you sure you want to cancel this invite?')) return

    try {
      await api.post(`/employer/invites/${inviteId}/cancel/`)
      setInvites(invites.map(i => i.id === inviteId ? { ...i, status: 'cancelled' } : i))
      alert('Invite cancelled')
    } catch (error) {
      console.error('Failed to cancel invite:', error)
      alert('Failed to cancel invite')
    }
  }

  const filteredInvites = filter === 'all'
    ? invites
    : invites.filter(i => i.status === filter)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sent': return 'bg-yellow-100 text-yellow-800'
      case 'accepted': return 'bg-green-100 text-green-800'
      case 'declined': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Sent Invites</h1>
        <a
          href="/candidates"
          className="px-4 py-2 bg-brand-600 text-white rounded hover:bg-brand-700"
        >
          Send New Invite
        </a>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {(['all', 'sent', 'accepted', 'declined'] as const).map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded capitalize ${
              filter === status
                ? 'bg-brand-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {status}
          </button>
        ))}
      </div>

      {/* Invites List */}
      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : filteredInvites.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
          <p>No invites to show</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredInvites.map((invite) => (
            <div key={invite.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{invite.job_title}</h3>
                  <p className="text-sm text-gray-500">
                    {invite.candidate_name} ({invite.candidate_email})
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(invite.status)}`}>
                    {invite.status}
                  </span>
                  {invite.status === 'sent' && (
                    <button
                      onClick={() => handleCancel(invite.id)}
                      className="px-3 py-1 text-red-600 hover:bg-red-50 rounded"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>

              <div className="text-sm text-gray-600">
                <p>Sent: {new Date(invite.sent_at).toLocaleDateString()}</p>
                {invite.accepted_at && (
                  <p>Accepted: {new Date(invite.accepted_at).toLocaleDateString()}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
