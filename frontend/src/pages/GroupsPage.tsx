import { useEffect, useState } from "react"
import {
  Stethoscope,
  Users,
  ShieldCheck,
  FileText,
  Plus,
  Pencil,
  Trash2,
  UserPlus,
  Check,
  X,
} from "lucide-react"

import {
  getGroups,
  createGroup,
  addGroupMember,
  getGroupMembers,
  updateGroupPermissions,
  getGroupResources,
  createGroupResource,
  updateGroupResource,
  deleteGroupResource,
} from "../services/api"

import "./GroupsPage.css"

type Group = {
  id: number
  name: string
  owner_id: number
}

type Member = {
  user_id: number
  username: string
  email: string
  can_view: boolean
  can_create: boolean
  can_edit: boolean
  can_delete: boolean
  can_manage_members: boolean
}

type Resource = {
  id: number
  title: string
  description: string
}

type Props = {
  token: string
}

type Permission =
  | "can_view"
  | "can_create"
  | "can_edit"
  | "can_delete"
  | "can_manage_members"

const permissionLabels: { key: Permission; label: string }[] = [
  { key: "can_view", label: "View" },
  { key: "can_create", label: "Create" },
  { key: "can_edit", label: "Edit" },
  { key: "can_delete", label: "Delete" },
  { key: "can_manage_members", label: "Manage members" },
]

export default function GroupsPage({ token }: Props) {
  const [groups, setGroups] = useState<Group[]>([])
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null)
  const [members, setMembers] = useState<Member[]>([])
  const [resources, setResources] = useState<Resource[]>([])

  const [canManageMembers, setCanManageMembers] = useState(false)

  const [groupName, setGroupName] = useState("")
  const [memberEmail, setMemberEmail] = useState("")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [editingResource, setEditingResource] = useState<number | null>(null)

  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function loadGroups() {
    const response = await getGroups(token)
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || "Could not load groups")
    }

    setGroups(data)
  }

  async function loadGroupData(groupId: number) {
    const [memberResponse, resourceResponse] = await Promise.all([
      getGroupMembers(token, groupId),
      getGroupResources(token, groupId),
    ])

    const memberData = await memberResponse.json()
    const resourceData = await resourceResponse.json()

    setCanManageMembers(memberResponse.ok)

    if (memberResponse.ok) {
      setMembers(memberData)
    } else {
      setMembers([])
    }

    if (resourceResponse.ok) {
      setResources(resourceData)
    } else {
      setResources([])
    }
  }

  useEffect(() => {
    loadGroups().catch((err) => {
      setError(err.message)
    })
  }, [token])

  useEffect(() => {
    if (selectedGroup !== null) {
      loadGroupData(selectedGroup).catch((err) => {
        setError(err.message)
      })
    }
  }, [selectedGroup, token])

  async function handleCreateGroup() {
    setError("")
    setMessage("")
    setLoading(true)

    try {
      const response = await createGroup(token, groupName)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Group creation failed")
      }

      setGroupName("")
      setMessage("Group created successfully.")
      await loadGroups()
      setSelectedGroup(data.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  async function handleAddMember() {
    if (selectedGroup === null) return

    setError("")
    setMessage("")
    setLoading(true)

    try {
      const response = await addGroupMember(token, selectedGroup, memberEmail)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Could not add member")
      }

      setMemberEmail("")
      setMessage("Member added successfully.")
      await loadGroupData(selectedGroup)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  async function handlePermissionChange(
    member: Member,
    permission: Permission,
    checked: boolean,
  ) {
    if (selectedGroup === null) return

    setError("")
    setMessage("")

    const updated = {
      can_view: member.can_view,
      can_create: member.can_create,
      can_edit: member.can_edit,
      can_delete: member.can_delete,
      can_manage_members: member.can_manage_members,
      [permission]: checked,
    }

    try {
      const response = await updateGroupPermissions(
        token,
        selectedGroup,
        member.user_id,
        updated,
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Permission update failed")
      }

      await loadGroupData(selectedGroup)
      setMessage("Permissions updated.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  async function handleSaveResource() {
    if (selectedGroup === null) return

    setError("")
    setMessage("")
    setLoading(true)

    try {
      const response =
        editingResource === null
          ? await createGroupResource(token, selectedGroup, title, description)
          : await updateGroupResource(
              token,
              selectedGroup,
              editingResource,
              title,
              description,
            )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Resource save failed")
      }

      setTitle("")
      setDescription("")
      setEditingResource(null)
      setMessage("Resource saved successfully.")
      await loadGroupData(selectedGroup)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  async function handleDeleteResource(resourceId: number) {
    if (selectedGroup === null) return
    if (!window.confirm("Delete this resource?")) return

    setError("")
    setMessage("")

    try {
      const response = await deleteGroupResource(
        token,
        selectedGroup,
        resourceId,
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Resource deletion failed")
      }

      await loadGroupData(selectedGroup)
      setMessage("Resource deleted.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  const selected = groups.find((group) => group.id === selectedGroup)
  const owner = members.find((member) => member.user_id === selected?.owner_id)
  const regularMembers = members.filter(
    (member) => member.user_id !== selected?.owner_id,
  )

  return (
    <div className="groups-page">
      <div className="groups-heading">
        <div className="groups-heading-icon">
          <Stethoscope size={25} />
        </div>
        <div>
          <h2>Groups &amp; Teams</h2>
          <p>Manage healthcare teams, members and shared resources.</p>
        </div>
      </div>

      {message && (
        <div className="groups-alert groups-success">
          <Check size={17} />
          {message}
        </div>
      )}

      {error && (
        <div className="groups-alert groups-error">
          <X size={17} />
          {error}
        </div>
      )}

      <section className="groups-card">
        <div className="groups-section-heading">
          <div className="groups-section-icon">
            <Plus size={19} />
          </div>
          <div>
            <h3>Create a group</h3>
            <p>Create a team for shared work and resources.</p>
          </div>
        </div>

        <form
          className="groups-create-form"
          onSubmit={(event) => {
            event.preventDefault()
            handleCreateGroup()
          }}
        >
          <input
            value={groupName}
            onChange={(event) => setGroupName(event.target.value)}
            placeholder="Enter group name"
            aria-label="Group name"
          />
          <button
            className="groups-primary-btn"
            type="submit"
            disabled={!groupName.trim() || loading}
          >
            <Plus size={17} />
            Create Group
          </button>
        </form>
      </section>

      <section className="groups-card">
        <div className="groups-section-heading">
          <div className="groups-section-icon">
            <Users size={19} />
          </div>
          <div>
            <h3>Your groups</h3>
            <p>Select a group to manage its team and resources.</p>
          </div>
        </div>

        {groups.length === 0 ? (
          <div className="groups-empty">
            <Users size={28} />
            <p>No groups yet</p>
            <span>Create your first group to get started.</span>
          </div>
        ) : (
          <div className="groups-list">
            {groups.map((group) => (
              <button
                type="button"
                key={group.id}
                onClick={() => setSelectedGroup(group.id)}
                className={`groups-list-item ${
                  selectedGroup === group.id ? "selected" : ""
                }`}
              >
                <span className="groups-list-icon">
                  <Stethoscope size={19} />
                </span>
                <span>{group.name}</span>
                {selectedGroup === group.id && (
                  <Check className="groups-selected-check" size={17} />
                )}
              </button>
            ))}
          </div>
        )}
      </section>

      {selectedGroup !== null && selected && (
        <>
          <section className="groups-card">
            <div className="groups-team-title">
              <div>
                <span className="groups-eyebrow">SELECTED TEAM</span>
                <h3>{selected.name}</h3>
              </div>
              <span className="groups-team-icon">
                <Users size={23} />
              </span>
            </div>

            <div className="groups-section-heading groups-subheading">
              <div className="groups-section-icon">
                <UserPlus size={19} />
              </div>
              <div>
                <h3>Add a member</h3>
                <p>Invite an existing AppointHUB user by email.</p>
              </div>
            </div>

            {canManageMembers ? (
              <form
                className="groups-create-form"
                onSubmit={(event) => {
                  event.preventDefault()
                  handleAddMember()
                }}
              >
                <input
                  type="email"
                  value={memberEmail}
                  onChange={(event) => setMemberEmail(event.target.value)}
                  placeholder="Member email address"
                  aria-label="Member email"
                />
                <button
                  className="groups-primary-btn"
                  type="submit"
                  disabled={!memberEmail.trim() || loading}
                >
                  <UserPlus size={17} />
                  Add Member
                </button>
              </form>
            ) : (
              <p className="groups-muted-note">
                You do not have permission to manage this group's members.
              </p>
            )}
          </section>

          <section className="groups-card">
            <div className="groups-section-heading">
              <div className="groups-section-icon">
                <ShieldCheck size={19} />
              </div>
              <div>
                <h3>Team members &amp; permissions</h3>
                <p>Control what each member can do in this group.</p>
              </div>
            </div>

            {owner && (
              <div className="groups-owner-card">
                <div className="groups-member-avatar">
                  <ShieldCheck size={20} />
                </div>
                <div className="groups-member-info">
                  <strong>{owner.username}</strong>
                  <span>{owner.email}</span>
                </div>
                <span className="groups-owner-badge">Group Owner</span>
                <p className="groups-owner-description">
                  Full permissions
                </p>
              </div>
            )}

            {canManageMembers ? (
              regularMembers.length === 0 ? (
                <div className="groups-empty groups-small-empty">
                  <Users size={25} />
                  <p>No other members yet</p>
                  <span>Add members to this group to manage their permissions.</span>
                </div>
              ) : (
                <div className="groups-members-list">
                  {regularMembers.map((member) => (
                    <div className="groups-member-card" key={member.user_id}>
                      <div className="groups-member-top">
                        <div className="groups-member-avatar">
                          <Users size={19} />
                        </div>
                        <div className="groups-member-info">
                          <strong>{member.username}</strong>
                          <span>{member.email}</span>
                        </div>
                      </div>

                      <div className="groups-permissions">
                        {permissionLabels.map(({ key, label }) => (
                          <label
                            className="groups-permission-option"
                            key={key}
                          >
                            <input
                              type="checkbox"
                              checked={member[key]}
                              disabled={!canManageMembers}
                              onChange={(event) =>
                                handlePermissionChange(
                                  member,
                                  key,
                                  event.target.checked,
                                )
                              }
                            />
                            <span>{label}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )
            ) : (
              <p className="groups-muted-note">
                Member details are available to users with member-management permission.
              </p>
            )}
          </section>

          <section className="groups-card">
            <div className="groups-section-heading">
              <div className="groups-section-icon">
                <FileText size={19} />
              </div>
              <div>
                <h3>Shared resources</h3>
                <p>Share useful information with your team.</p>
              </div>
            </div>

            <form
              className="groups-resource-form"
              onSubmit={(event) => {
                event.preventDefault()
                handleSaveResource()
              }}
            >
              <input
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Resource title"
                aria-label="Resource title"
              />
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Write a short description..."
                aria-label="Resource description"
                rows={3}
              />
              <div className="groups-form-actions">
                <button
                  className="groups-primary-btn"
                  type="submit"
                  disabled={!title.trim() || loading}
                >
                  <Check size={17} />
                  {editingResource === null ? "Create Resource" : "Save Changes"}
                </button>

                {editingResource !== null && (
                  <button
                    className="groups-secondary-btn"
                    type="button"
                    onClick={() => {
                      setEditingResource(null)
                      setTitle("")
                      setDescription("")
                    }}
                  >
                    Cancel
                  </button>
                )}
              </div>
            </form>

            {resources.length === 0 ? (
              <div className="groups-empty groups-small-empty">
                <FileText size={25} />
                <p>No shared resources yet</p>
                <span>Resources shared with this team will appear here.</span>
              </div>
            ) : (
              <div className="groups-resources-list">
                {resources.map((resource) => (
                  <article className="groups-resource-card" key={resource.id}>
                    <div className="groups-resource-icon">
                      <FileText size={21} />
                    </div>
                    <div className="groups-resource-content">
                      <h4>{resource.title}</h4>
                      <p>{resource.description}</p>
                    </div>
                    <div className="groups-resource-actions">
                      <button
                        type="button"
                        className="groups-icon-btn"
                        aria-label={`Edit ${resource.title}`}
                        title="Edit resource"
                        onClick={() => {
                          setEditingResource(resource.id)
                          setTitle(resource.title)
                          setDescription(resource.description)
                        }}
                      >
                        <Pencil size={17} />
                      </button>
                      <button
                        type="button"
                        className="groups-icon-btn groups-delete-btn"
                        aria-label={`Delete ${resource.title}`}
                        title="Delete resource"
                        onClick={() => handleDeleteResource(resource.id)}
                      >
                        <Trash2 size={17} />
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}