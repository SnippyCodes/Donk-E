import React, { useState, useRef, useEffect } from 'react'
import { ChevronDown, Check, Lock } from 'lucide-react'

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
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const formatRole = (role: string) => {
    return role.replace(/_/g, ' ')
  }

  // Get initials for avatar
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <div className="user-picker-wrapper" ref={dropdownRef} style={{ position: 'relative' }}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          height: '32px',
          padding: '0 10px',
          background: '#121215',
          border: '1px solid #27272a',
          borderRadius: '6px',
          cursor: 'pointer',
          color: '#f4f4f5',
          fontSize: '12px',
          fontWeight: 500,
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '6px',
          whiteSpace: 'nowrap',
          lineHeight: '1',
          userSelect: 'none',
          transition: 'all 0.15s ease',
          boxShadow: 'inset 0 1px 0 0 rgba(255, 255, 255, 0.04)',
        }}
        title="Switch active operator identity (Strict scope & memory isolation)"
      >
        {/* Avatar Initials */}
        <div style={{
          width: '18px',
          height: '18px',
          borderRadius: '4px',
          background: '#27272a',
          color: '#f59e0b',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '9.5px',
          fontWeight: 700,
          fontFamily: "'JetBrains Mono', monospace",
          flexShrink: 0
        }}>
          {getInitials(currentUser.name)}
        </div>

        <span style={{ fontWeight: 600, color: '#f4f4f5' }}>{currentUser.name}</span>

        <span style={{
          fontSize: '10px',
          color: '#71717a',
          fontFamily: "'JetBrains Mono', monospace",
          background: '#09090b',
          border: '1px solid #27272a',
          padding: '2px 5px',
          borderRadius: '3px',
        }}>
          {currentUser.user_id}
        </span>

        {/* Green Privacy Lock Icon */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '3px',
          color: '#10b981',
          fontSize: '10px',
          fontFamily: "'JetBrains Mono', monospace"
        }} title="Private Memory & Rule Scope Isolated to Current Operator">
          <Lock size={11} style={{ flexShrink: 0 }} />
          <span>Isolated</span>
        </div>

        <ChevronDown size={12} color="#71717a" style={{ flexShrink: 0, marginLeft: '2px' }} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div style={{
          position: 'absolute',
          top: '38px',
          right: 0,
          width: '320px',
          background: '#121215',
          border: '1px solid #27272a',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.8), inset 0 1px 0 0 rgba(255, 255, 255, 0.05)',
          borderRadius: '8px',
          padding: '6px',
          zIndex: 100,
          display: 'flex',
          flexDirection: 'column',
          gap: '4px'
        }}>
          <div style={{
            padding: '6px 10px',
            fontSize: '10.5px',
            fontFamily: "'JetBrains Mono', monospace",
            textTransform: 'uppercase',
            letterSpacing: '0.4px',
            color: '#71717a',
            borderBottom: '1px solid #1f1f23',
            marginBottom: '4px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span>Field Operator Session</span>
            <span style={{ color: '#10b981' }}>WHERE user_id = ?</span>
          </div>

          <div style={{ maxHeight: '280px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '2px' }}>
            {users.map(u => {
              const isSelected = u.user_id === currentUser.user_id
              return (
                <div
                  key={u.user_id}
                  onClick={() => {
                    onSelectUser(u)
                    setIsOpen(false)
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    background: isSelected ? '#18181b' : 'transparent',
                    border: isSelected ? '1px solid #27272a' : '1px solid transparent',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={e => {
                    if (!isSelected) e.currentTarget.style.background = '#18181b'
                  }}
                  onMouseLeave={e => {
                    if (!isSelected) e.currentTarget.style.background = 'transparent'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{
                      width: '24px',
                      height: '24px',
                      borderRadius: '4px',
                      background: isSelected ? '#f59e0b' : '#27272a',
                      color: isSelected ? '#09090b' : '#a1a1aa',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '10px',
                      fontWeight: 700,
                      fontFamily: "'JetBrains Mono', monospace"
                    }}>
                      {getInitials(u.name)}
                    </div>
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: '#f4f4f5' }}>
                        {u.name}
                      </div>
                      <div style={{
                        fontSize: '10px',
                        color: '#71717a',
                        textTransform: 'capitalize',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <span>{formatRole(u.role)}</span>
                        {u.team_id && <span>· {u.team_id}</span>}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{
                      fontSize: '10px',
                      fontFamily: "'JetBrains Mono', monospace",
                      color: '#a1a1aa',
                      background: '#09090b',
                      padding: '1px 5px',
                      borderRadius: '3px',
                      border: '1px solid #1f1f23'
                    }}>
                      {u.user_id}
                    </span>
                    {isSelected && <Check size={14} color="#10b981" />}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
