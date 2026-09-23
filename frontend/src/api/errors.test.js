import test from 'node:test'
import assert from 'node:assert/strict'
import { apiError } from './errors.js'

test('network failure is not presented as an invalid password', () => {
  assert.match(apiError(new Error('Network Error')), /conectar ao servidor/)
})
test('field validation keeps actionable messages with Portuguese labels', () => {
  const error = { response: { status: 400, data: { email: ['Este e-mail já está cadastrado.'] } } }
  assert.equal(apiError(error), 'E-mail: Este e-mail já está cadastrado.')
})
test('server errors do not expose HTML or technical internals', () => {
  assert.match(apiError({ response: { status: 500, data: '<html>traceback</html>' } }), /temporariamente indisponível/)
})
test('rate limits give a specific retry instruction', () => {
  assert.match(apiError({ response: { status: 429, data: {} } }), /Muitas tentativas/)
})
