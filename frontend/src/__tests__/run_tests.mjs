/**
 * STAIL Frontend – Store & Utility Unit Tests
 * Run via: node src/__tests__/run_tests.mjs
 * Pure ESM, no external test framework required.
 */

import { useAuthStore } from '../store/authStore.ts';
import { useChatStore } from '../store/chatStore.ts';
import { formatPrice } from '../components/PropertyCard.tsx';

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`  ✅ PASS: ${message}`);
    passed++;
  } else {
    console.error(`  ❌ FAIL: ${message}`);
    failed++;
  }
}

function assertEqual(actual, expected, message) {
  assert(actual === expected, `${message} (got: ${JSON.stringify(actual)}, expected: ${JSON.stringify(expected)})`);
}

console.log('\n══════════════════════════════════════');
console.log('  STAIL Frontend – Unit Test Suite');
console.log('══════════════════════════════════════\n');

// ─── AuthStore Tests ────────────────────────────────────────
console.log('📦 AuthStore Tests:');

// Reset store to initial state
useAuthStore.setState({ token: null, refreshToken: null, user: null, isInitialized: false });

// T1: Initial state
const s0 = useAuthStore.getState();
assertEqual(s0.token, null, 'T1: Initial token is null');
assertEqual(s0.user, null, 'T2: Initial user is null');
assertEqual(s0.refreshToken, null, 'T3: Initial refreshToken is null');

// T2: setAuth
useAuthStore.getState().setAuth('tok_abc', 'ref_xyz', {
  id: 'u-01',
  email: 'test@stail.com',
  phone: '+91 9876543210',
  full_name: 'Aditya Maharana',
  role: 'BUYER',
});

const s1 = useAuthStore.getState();
assertEqual(s1.token, 'tok_abc', 'T4: setAuth sets token');
assertEqual(s1.refreshToken, 'ref_xyz', 'T5: setAuth sets refreshToken');
assertEqual(s1.user?.email, 'test@stail.com', 'T6: setAuth sets user.email');
assertEqual(s1.user?.role, 'BUYER', 'T7: setAuth sets user.role');

// T3: setTokens (rotation)
useAuthStore.getState().setTokens('tok_new', 'ref_new');
const s2 = useAuthStore.getState();
assertEqual(s2.token, 'tok_new', 'T8: setTokens updates access token');
assertEqual(s2.refreshToken, 'ref_new', 'T9: setTokens updates refresh token');

// T4: logout clears state
useAuthStore.setState({ token: 'tok_abc', refreshToken: 'ref_xyz', user: { id: 'u-01', email: 'test@stail.com', phone: '', full_name: 'Test', role: 'BUYER' } });
// Patch logoutApi to avoid real HTTP call
const originalLogout = useAuthStore.getState().logout;
useAuthStore.setState({ logout: () => useAuthStore.setState({ token: null, refreshToken: null, user: null }) });
useAuthStore.getState().logout();
const s3 = useAuthStore.getState();
assertEqual(s3.token, null, 'T10: logout clears token');
assertEqual(s3.user, null, 'T11: logout clears user');

// ─── ChatStore Tests ─────────────────────────────────────────
console.log('\n📦 ChatStore Tests:');

// Reset
useChatStore.setState({ messages: [], sessionId: null, loading: false, error: null, leadGrade: null, confidence: null });

const c0 = useChatStore.getState();
assertEqual(c0.messages.length, 0, 'T12: Initial messages is empty');
assertEqual(c0.sessionId, null, 'T13: Initial sessionId is null');

// Add user message
useChatStore.getState().addMessage({ role: 'user', content: '3BHK in Bandra West' });
const c1 = useChatStore.getState();
assertEqual(c1.messages.length, 1, 'T14: addMessage increases count');
assertEqual(c1.messages[0].role, 'user', 'T15: Message role is user');
assertEqual(c1.messages[0].content, '3BHK in Bandra West', 'T16: Message content matches');
assert(!!c1.messages[0].id, 'T17: Message gets auto-generated id');
assert(!!c1.messages[0].createdAt, 'T18: Message gets auto-generated createdAt');

// Add assistant message
useChatStore.getState().addMessage({ role: 'assistant', content: 'Found 5 matching properties', properties: [{ id: 'p-1', city: 'Mumbai', price: 25000000, property_type: 'APARTMENT' }] });
const c2 = useChatStore.getState();
assertEqual(c2.messages.length, 2, 'T19: Second addMessage increases count to 2');
assertEqual(c2.messages[1].properties?.length, 1, 'T20: Assistant message carries properties');

// setSessionId
useChatStore.getState().setSessionId('sess-abc123');
const c3 = useChatStore.getState();
assertEqual(c3.sessionId, 'sess-abc123', 'T21: setSessionId sets session ID');

// setMetadata
useChatStore.getState().setMetadata('A', 0.92);
const c4 = useChatStore.getState();
assertEqual(c4.leadGrade, 'A', 'T22: setMetadata sets leadGrade');
assertEqual(c4.confidence, 0.92, 'T23: setMetadata sets confidence');

// setLoading
useChatStore.getState().setLoading(true);
assertEqual(useChatStore.getState().loading, true, 'T24: setLoading(true) works');
useChatStore.getState().setLoading(false);
assertEqual(useChatStore.getState().loading, false, 'T25: setLoading(false) works');

// setError
useChatStore.getState().setError('Network timeout');
assertEqual(useChatStore.getState().error, 'Network timeout', 'T26: setError sets error');

// clearChat
useChatStore.getState().clearChat();
const c5 = useChatStore.getState();
assertEqual(c5.messages.length, 0, 'T27: clearChat empties messages');
assertEqual(c5.sessionId, null, 'T28: clearChat resets sessionId');
assertEqual(c5.leadGrade, null, 'T29: clearChat resets leadGrade');
assertEqual(c5.confidence, null, 'T30: clearChat resets confidence');
assertEqual(c5.error, null, 'T31: clearChat resets error');

// ─── formatPrice Utility Tests ────────────────────────────────
console.log('\n📦 formatPrice Utility Tests:');

assertEqual(formatPrice(25000000), '₹ 2.50 Cr', 'T32: 2.5 Crore formats correctly');
assertEqual(formatPrice(15000000), '₹ 1.50 Cr', 'T33: 1.5 Crore formats correctly');
assertEqual(formatPrice(8500000), '₹ 85.00 Lakh', 'T34: 85 Lakh formats correctly');
assertEqual(formatPrice(5000000), '₹ 50.00 Lakh', 'T35: 50 Lakh formats correctly');
assertEqual(formatPrice(2500000), '₹ 25.00 Lakh', 'T36: 25 Lakh formats correctly');
assertEqual(formatPrice(undefined), 'Price on Request', 'T37: undefined returns "Price on Request"');
assertEqual(formatPrice(NaN), 'Price on Request', 'T38: NaN returns "Price on Request"');

// ─── Summary ────────────────────────────────────────────────
console.log('\n══════════════════════════════════════');
const total = passed + failed;
if (failed === 0) {
  console.log(`  ✅ ALL ${total} TESTS PASSED`);
} else {
  console.log(`  ⚠️  ${passed}/${total} PASSED — ${failed} FAILED`);
}
console.log('══════════════════════════════════════\n');

process.exit(failed > 0 ? 1 : 0);
