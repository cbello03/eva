"use client";

import {
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Typography,
  Paper,
} from "@mui/material";
import { Person as PersonIcon } from "@mui/icons-material";
import type { GroupMember } from "../api";

interface GroupMembersProps {
  members: GroupMember[];
}

export default function GroupMembers({ members }: GroupMembersProps) {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        Miembros del grupo ({members.length})
      </Typography>
      <List dense disablePadding>
        {members.map((member) => (
          <ListItem key={member.id} disableGutters>
            <ListItemAvatar>
              <Avatar sx={{ width: 32, height: 32 }}>
                <PersonIcon fontSize="small" />
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={member.display_name}
              secondary={`Se unió el ${new Date(member.joined_at).toLocaleDateString()}`}
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
}
