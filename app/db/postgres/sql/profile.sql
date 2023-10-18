-- name: get_gens_for_owner
SELECT
	g.id,
  g.user_id,
  (
    SELECT username FROM auth_user WHERE id = g.user_id
  ),
	g.title,
  g.access,
	g.views,
	g.active,
  (
    SELECT
      count(*)
    FROM
      gen_like
    WHERE
      g.id = gen_id
  ) AS likes_count,
	(
    SELECT
      count(*)
    FROM
      gen_fav
    WHERE
      g.id = gen_id
  ) AS favs_count
FROM
	gen g
WHERE 
	g.user_id = $1
	AND g.active = True
ORDER BY g.date_updated DESC;


-- name: get_gens_for_guest
SELECT
	g.id,
  g.user_id,
  (
    SELECT username FROM auth_user WHERE id = g.user_id
  ),
	g.title,
  g.access,
	g.views,
	g.active,
  (
    SELECT
      COUNT(*)
    FROM
      gen_like
    WHERE
      g.id = gen_id
  ) AS likes_count,
	(
    SELECT
      COUNT(*)
    FROM
      gen_fav
    WHERE
      g.id = gen_id
  ) AS favs_count
FROM
	gen g
WHERE 
	g.user_id = $1
	AND g.active = True
	AND g.access = 0
ORDER BY g.date_updated DESC;

-- name: get_lists_for_owner
SELECT
  l.*,
  (
    SELECT username FROM auth_user WHERE id = l.user_id
  )
FROM
	list l
WHERE 
  l.user_id = $1
	AND l.active = True
ORDER BY l.id DESC;

-- name: get_lists_for_guest
SELECT
	l.id,
  l.user_id,
  (
    SELECT username FROM auth_user WHERE id = l.user_id
  ),
	l.title,
	l.description,
  l.access,
	l.active
FROM
	list l
WHERE 
	l.user_id = $1
	AND l.active = True
	AND l.access = 0
ORDER BY l.id DESC;

-- name: get_gens_fav
SELECT
	g.id,
  g.user_id,
  (
    SELECT username FROM auth_user WHERE id = g.user_id
  ),
	g.title,
  g.access,
	g.views,
	g.active,
  (
    SELECT
      count(*)
    FROM
      gen_like
    WHERE
      g.id = gen_id
  ) AS likes_count,
	(
    SELECT
      count(*)
    FROM
      gen_fav
    WHERE
      g.id = gen_id
  ) AS favs_count
FROM 
  gen_fav gf
JOIN gen g
  ON g.active = True
  AND g.access = 0
  AND g.id = gf.gen_id
WHERE
  gf.user_id = $1
ORDER BY gf.id DESC;

-- name: create_notification
INSERT INTO profile_notification
  (user_id, message, created_at)
VALUES ($1, $2, $3);