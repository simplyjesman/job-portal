import { useState, useEffect } from 'react'
import api from '../services/api'

interface InterviewInvite {
  id: number
  job_title: string
  job_description: string
  employer_name: string
  salary_min?: number
  salary_max?: number
  location?: string
  message?: string
  status: 'sent' | 'accepted' | 'declined'
  sent_at: string
}

export default function InvitesPage() {
  const [pendingInvites, setPendingInvites] = useState<InterviewInvite[]>([])
  const [acceptedInvites, setAcceptedInvites] = useState<InterviewInvite[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'pending' | 'accepted'>('pending')
  const [respondingId, setRespondingId] = useState<number | null>(null)

  useEffect(() => {
    fetchInvites()
  }, [])

  const fetchInvites = async () => {
    setLoading(true)
    try {
      const [pendingRes, acceptedRes] = await Promise.all([
        api.get('/candidate/invites/pending/'),
        api.get('/candidate/invites/accepted/'),
      ])
      setPendingInvites(pendingRes.data)
      setAcceptedInvites(acceptedRes.data)
    } catch (error) {
      console.error('Failed to fetch invites:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRespond = async (inviteId: number, action: 'accept' | 'decline') => {
    setRespondingId(inviteId)
    try {
      await api.post(`/candidate/invites/${inviteId}/respond/`, { action })
      alert(`Invite ${action}ed!`)
      fetchInvites()
      setRespondingId(null)
    } catch (error) {
      console.error(`Failed to ${action} invite:`, error)
      alert(`Failed to ${action} invite`)
      setRespondingId(null)
    }
  }

  const invites = tab === 'pending' ? pendingInvites : acceptedInvites

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Interview Invites</h1>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setTab('pending')}
          className={`px-4 py-2 font-medium ${
            tab === 'pending'
              ? 'text-brand-600 border-b-2 border-brand-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Pending ({pendingInvites.length})
        </button>
        <button
          onClick={() => setTab('accepted')}
          className={`px-4 py-2 font-medium ${
            tab === 'accepted'
              ? 'text-brand-600 border-b-2 border-brand-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Accepted ({acceptedInvites.length})
        </button>
      </div>

      {/* Invites List */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading invites...</div>
      ) : invites.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 text-lg">
            {tab === 'pending' ? 'No pending invites yet' : 'No accepted invites yet'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {invites.map((invite) => (
            <div key={invite.id} className="bg-white rounded-lg shadow p-6 space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{invite.job_title}</h2>
                  <p className="text-lg text-brand-600 font-medium">{invite.employer_name}</p>
                </div>
                {invite.status === 'accepted' && (
                  <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                    Accepted
                  </span>
                )}
              </div>

              <div className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap text-gray-700">{invite.job_description}</p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                {invite.salary_min && invite.salary_max && (
                  <div>
                    <p className="text-gray-500">Salary</p>
                    <p className="font-medium text-gray-900">
                      £{invite.salary_min.toLocaleString()} - £{invite.salary_max.toLocaleString()}
                    </p>
                  </div>
                )}
                {invite.location && (
                  <div>
                    <p className="text-gray-500">Location</p>
                    <p className="font-medium text-gray-900">{invite.location}</p>
                  </div>
                )}
                <div>
                  <p className="text-gray-500">Received</p>
                  <p className="font-medium text-gray-900">{new Date(invite.sent_at).toLocaleDateString()}</p>
                </div>
              </div>

              {invite.message && (
                <div className="bg-blue-50 p-4 rounded border border-blue-200">
                  <p className="text-sm font-medium text-gray-900 mb-2">Message from employer:</p>
                  <p className="text-gray-700">{invite.message}</p>
                </div>
              )}

              {tab === 'pending' && (
                <div className="flex gap-3 justify-end">
                  <button
                    onClick={() => handleRespond(invite.id, 'decline')}
                    disabled={respondingId === invite.id}
                    className="px-6 py-2 bg-gray-200 text-gray-900 rounded hover:bg-gray-300 disabled:bg-gray-400"
                  >
                    Decline
                  </button>
                  <button
                    onClick={() => handleRespond(invite.id, 'accept')}
                    disabled={respondingId === invite.id}
                    className="px-6 py-2 bg-brand-600 text-white rounded hover:bg-brand-700 disabled:bg-gray-400"
                  >
                    {respondingId === invite.id ? 'Processing...' : 'Accept'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
