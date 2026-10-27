# The connected publisher verifies central owner tokens before dispatch/promotion.
# This private-repository-independent job guard enforces the bounded lease window.
import datetime
expires=datetime.datetime.fromisoformat('2026-10-27T14:22:30.085Z'.replace('Z','+00:00'))
assert datetime.datetime.now(datetime.timezone.utc)<expires,'Publisher lease window expired; connected owner must reconcile before resume'
print('Publisher lease window valid; connected session owns token verification')
