// Where the assistant conversations are kept: on the server for each user, or in this browser when the app
// runs on DuckDB in the browser (the data, and the questions about it, never leave the machine).
import api from '../services/api';
import { useEngine } from '../engine';

const STORAGE_KEY = 'datalakeStudio.conversations';
// localStorage holds a few MB: fewer conversations than the server keeps
const MAX_LOCAL = 50;

function onServer() {
  return useEngine().mode === 'remote';
}

// Every conversation, with its messages: { id: conversation }
function readLocal() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch (_) {
    return {};
  }
}

function writeLocal(conversations) {
  const kept = Object.values(conversations).sort((a, b) => b.updated - a.updated).slice(0, MAX_LOCAL);
  // Throws when the browser storage is full: the caller reports it
  localStorage.setItem(STORAGE_KEY, JSON.stringify(Object.fromEntries(kept.map((c) => [c.id, c]))));
}

const summary = ({ messages, ...conversation }) => conversation; // eslint-disable-line no-unused-vars

// The conversations without their messages, most recent first
export async function listConversations() {
  if (onServer()) return (await api.get('/conversations')).data;
  return Object.values(readLocal()).map(summary).sort((a, b) => b.updated - a.updated);
}

export async function getConversation(id) {
  if (onServer()) return (await api.get(`/conversations/${id}`)).data;
  const conversation = readLocal()[id];
  if (!conversation) throw new Error(`Conversation ${id} not found`);
  return conversation;
}

// Saves the conversation and returns it without its messages
export async function saveConversation(id, { title, messages }) {
  if (onServer()) return (await api.put(`/conversations/${id}`, { title, messages })).data;
  const conversations = readLocal();
  const now = Date.now() / 1000;
  conversations[id] = { id, title, database: null, created: conversations[id]?.created ?? now, updated: now, messages };
  writeLocal(conversations);
  return summary(conversations[id]);
}

export async function renameConversation(id, title) {
  if (onServer()) return (await api.patch(`/conversations/${id}`, { title })).data;
  const conversations = readLocal();
  if (!conversations[id]) throw new Error(`Conversation ${id} not found`);
  conversations[id].title = title;
  writeLocal(conversations);
  return summary(conversations[id]);
}

export async function deleteConversation(id) {
  if (onServer()) {
    await api.delete(`/conversations/${id}`);
    return;
  }
  const conversations = readLocal();
  delete conversations[id];
  writeLocal(conversations);
}
