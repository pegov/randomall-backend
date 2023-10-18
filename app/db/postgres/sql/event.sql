-- name: search
SELECT
  e.*,
  (
    SELECT username FROM auth_user WHERE id = e.user_id
  )
FROM
  user_event e
WHERE
  ($3::integer IS NULL OR e.user_id = $3::integer)
LIMIT $2::integer OFFSET $1::integer;

-- name: search_count
SELECT
  COUNT(1)
FROM
  user_event e
WHERE
  ($3::integer IS NULL OR e.user_id = $3::integer)
LIMIT $2::integer OFFSET $1::integer;