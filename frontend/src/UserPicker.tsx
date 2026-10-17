import React from 'react'
import { User } from 'lucide-react'

export interface UserOption {
  user_id: string
  name: string
  role: string
  team_id?: string
}

interface UserPickerProps {
  currentUser: UserOption
  users: UserOption[]
  onSelectUser: (user: UserOption) => void
}

export const UserPicker: React.FC<UserPickerProps> = ({ currentUser, users, onSelectUser }) => {
  return (
    <div className="user-picker-wrapper" id="user-picker">
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        background: 'rgba(255, 255, 255, 0.04)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '24px',
        padding: '4px 14px 4px 10px',
        fontSize: '12px',
      }}>
        <div style={{
          width: '24px',
          height: '24px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #6366f1, #a855f7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: '10px',
          fontWeight: 700
        }}>
          <User size={12} />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{currentUser.name}</span>
            <span style={{
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
              background: 'rgba(0,0,0,0.3)',
              padding: '1px 5px',
              borderRadius: '4px'
            }}>
              {currentUser.user_id}
            </span>
          </div>
          <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
            {currentUser.role.replace(/_/g, ' ')}
          </span>
        </div>

        <select
          value={currentUser.user_id}
          onChange={(e) => {
            const found = users.find(u => u.user_id === e.target.value)
            if (found) onSelectUser(found)
          }}
          style={{
            marginLeft: '8px',
            background: 'transparent',
            border: 'none',
            color: 'var(--color-brand)',
            fontSize: '12px',
            outline: 'none',
            cursor: 'pointer',
            fontWeight: 500
          }}
        >
          {users.map((u) => (
            <option key={u.user_id} value={u.user_id} style={{ background: '#111827', color: '#f8fafc' }}>
              Switch: {u.name} ({u.role.replace(/_/g, ' ')})
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
