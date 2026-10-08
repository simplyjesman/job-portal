import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import api from '../services/api'

interface WorkExperience {
  id: number
  company: string
  role: string
  start_date: string
  end_date?: string
  description?: string
  skills: Array<{ id: number; name: string }>
  is_current: boolean
}

interface Education {
  id: number
  institution: string
  degree: string
  field: string
  graduation_date: string
  description?: string
}

interface ExternalLink {
  id: number
  platform: 'github' | 'linkedin' | 'portfolio'
  username: string
  url: string
}

interface Profile {
  id: number
  email: string
  first_name_display: string
  last_name_display: string
  headline: string
  location: string
  availability: string
  experience_level: string
  photo?: string
  profile_status: 'draft' | 'live'
  published_at?: string
  work_history: WorkExperience[]
  education: Education[]
  external_links: ExternalLink[]
}

export default function ProfilePage() {
  const { id } = useParams<{ id?: string }>()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [editing, setEditing] = useState(false)
  const [isOwnProfile, setIsOwnProfile] = useState(false)

  useEffect(() => {
    fetchProfile()
  }, [id])

  const fetchProfile = async () => {
    setLoading(true)
    try {
      const endpoint = id ? `/candidates/${id}/profile/` : '/candidates/profile/'
      const res = await api.get(endpoint)
      setProfile(res.data)

      // Check if this is the user's own profile
      const token = localStorage.getItem('token')
      if (token && !id) {
        setIsOwnProfile(true)
      } else if (token && id) {
        // Extract user ID from token if available
        setIsOwnProfile(false)
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePublish = async () => {
    try {
      const res = await api.post('/candidates/profile/publish/', {})
      setProfile(res.data)
      alert('Profile is now live!')
    } catch (error: any) {
      alert(error.response?.data?.error || 'Failed to publish profile')
    }
  }

  const handleRevert = async () => {
    if (!confirm('Are you sure? You cannot revert if you have pending interviews.')) return
    try {
      const res = await api.post('/candidates/profile/revert/', {})
      setProfile(res.data)
      alert('Profile reverted to draft')
    } catch (error: any) {
      alert(error.response?.data?.error || 'Failed to revert profile')
    }
  }

  if (loading) return <div className="text-center py-12 text-gray-500">Loading profile...</div>
  if (!profile) return <div className="text-center py-12 text-gray-500">Profile not found</div>

  const platformIcons: Record<string, string> = {
    github: '🐙',
    linkedin: '💼',
    portfolio: '🌐'
  }

  const getAvailabilityLabel = (key: string) => {
    const labels: Record<string, string> = {
      immediate: 'Immediately',
      notice_1_week: '1 week',
      notice_2_weeks: '2 weeks',
      notice_1_month: '1 month',
      notice_3_months: '3+ months'
    }
    return labels[key] || key
  }

  const experienceLevelBadgeColor = {
    junior: 'bg-blue-100 text-blue-800',
    mid: 'bg-purple-100 text-purple-800',
    senior: 'bg-amber-100 text-amber-800',
    lead: 'bg-red-100 text-red-800'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start">
          <div className="flex gap-4">
            {profile.photo ? (
              <img src={profile.photo} alt={profile.first_name_display} className="w-20 h-20 rounded-full object-cover" />
            ) : (
              <div className="w-20 h-20 rounded-full bg-brand-200 flex items-center justify-center text-2xl font-bold text-brand-700">
                {profile.first_name_display[0]}{profile.last_name_display[0]}
              </div>
            )}
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {profile.first_name_display} {profile.last_name_display}
              </h1>
              {profile.headline && (
                <p className="text-lg text-gray-600 mt-1">{profile.headline}</p>
              )}
              <div className="flex gap-3 mt-3 items-center">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${experienceLevelBadgeColor[profile.experience_level as keyof typeof experienceLevelBadgeColor]}`}>
                  {profile.experience_level.charAt(0).toUpperCase() + profile.experience_level.slice(1)}
                </span>
                <span className="text-gray-600">📍 {profile.location}</span>
                <span className="text-gray-600">⏰ Notice: {getAvailabilityLabel(profile.availability)}</span>
              </div>
            </div>
          </div>

          {isOwnProfile && (
            <div className="space-y-2">
              {profile.profile_status === 'draft' && (
                <button
                  onClick={handlePublish}
                  className="w-full px-4 py-2 bg-brand-600 text-white rounded hover:bg-brand-700"
                >
                  Make Live
                </button>
              )}
              {profile.profile_status === 'live' && (
                <>
                  <div className="text-sm text-gray-600 text-right">
                    Published: {new Date(profile.published_at || '').toLocaleDateString()}
                  </div>
                  <button
                    onClick={handleRevert}
                    className="w-full px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400"
                  >
                    Make Draft
                  </button>
                </>
              )}
              <button
                onClick={() => setEditing(!editing)}
                className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                {editing ? 'Done' : 'Edit Profile'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {['overview', 'experience', 'education', 'links'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium capitalize ${
              activeTab === tab
                ? 'text-brand-600 border-b-2 border-brand-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">EMAIL</h3>
            <p className="text-gray-900">{profile.email}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">HEADLINE</h3>
            <p className="text-gray-900">{profile.headline || '—'}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">EXPERIENCE LEVEL</h3>
            <p className="text-gray-900 capitalize">{profile.experience_level}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">AVAILABILITY</h3>
            <p className="text-gray-900">{getAvailabilityLabel(profile.availability)}</p>
          </div>
          {profile.profile_status === 'live' && profile.published_at && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">PUBLISHED</h3>
              <p className="text-gray-900">{new Date(profile.published_at).toLocaleDateString()}</p>
            </div>
          )}
        </div>
      )}

      {/* Experience Tab */}
      {activeTab === 'experience' && (
        <div className="space-y-4">
          {profile.work_history.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
              No work experience added yet
            </div>
          ) : (
            profile.work_history.map((work) => (
              <div key={work.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{work.role}</h3>
                    <p className="text-brand-600 font-medium">{work.company}</p>
                    <p className="text-sm text-gray-600 mt-1">
                      {new Date(work.start_date).toLocaleDateString('en-GB', { year: 'numeric', month: 'short' })} –{' '}
                      {work.is_current ? 'Present' : new Date(work.end_date!).toLocaleDateString('en-GB', { year: 'numeric', month: 'short' })}
                    </p>
                  </div>
                  {work.is_current && (
                    <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                      Current
                    </span>
                  )}
                </div>
                {work.description && (
                  <p className="text-gray-700 mt-3 whitespace-pre-wrap text-sm">{work.description}</p>
                )}
                {work.skills.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {work.skills.map((skill) => (
                      <span key={skill.id} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                        {skill.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Education Tab */}
      {activeTab === 'education' && (
        <div className="space-y-4">
          {profile.education.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
              No education added yet
            </div>
          ) : (
            profile.education.map((edu) => (
              <div key={edu.id} className="bg-white rounded-lg shadow p-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{edu.degree}</h3>
                  <p className="text-brand-600 font-medium">{edu.institution}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {edu.field} • {new Date(edu.graduation_date).getFullYear()}
                  </p>
                </div>
                {edu.description && (
                  <p className="text-gray-700 mt-3 text-sm">{edu.description}</p>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Links Tab */}
      {activeTab === 'links' && (
        <div className="bg-white rounded-lg shadow p-6">
          {profile.external_links.length === 0 ? (
            <p className="text-gray-500 text-center">No links added yet</p>
          ) : (
            <div className="flex flex-wrap gap-4">
              {profile.external_links.map((link) => (
                <a
                  key={link.id}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
                >
                  <span className="text-xl">{platformIcons[link.platform]}</span>
                  <span className="text-gray-700 font-medium capitalize">{link.platform}</span>
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
