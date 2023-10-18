-- name: get_stats
SELECT
	(
		SELECT COUNT(*) FROM list WHERE active = True
	) AS active,
	(
		SELECT COUNT(*) FROM list WHERE active = False
	) AS inactive,
	(
		SELECT COUNT(*) FROM list WHERE access = 0
	) AS public,
	(
		SELECT COUNT(*) FROM list WHERE access = 1
	) AS private
;

-- name: get
SELECT
	l.*,
	(SELECT username FROM auth_user WHERE id = user_id)
FROM
	list l
WHERE
	l.id = $1;

-- name: create
INSERT INTO
	list(
		user_id,
		title,
		description,
		access,
		content,
		slicer,
		date_added,
		date_updated,
		active
	)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
RETURNING id;

-- name: update
UPDATE list SET
	title = $2,
	description = NULLIF($3, ''),
	access = $4,
	content = $5,
	slicer = $6,
	date_updated = COALESCE($7, date_updated)
WHERE
	id = $1;

-- name: search
SELECT
  l.id,
  l.user_id,
  (
    SELECT username FROM auth_user WHERE id = l.user_id
  ),
  l.title,
  l.description,
  l.access,
  l.date_added,
  l.date_updated,
  l.active
FROM
  list l
WHERE
  ($3::text IS NULL OR l.title iLIKE CONCAT('%', $3::text, '%'))
  AND ($4::int IS NULL OR l.access = $4::int)
GROUP BY l.id
ORDER BY {} {}
LIMIT $2::int OFFSET $1::int;

-- name: search_count
SELECT
  COUNT(1)
FROM list l
WHERE
  ($1::text IS NULL OR l.title iLIKE CONCAT('%', $1::text, '%'))
  AND ($2::int IS NULL OR l.access = $2::int);
