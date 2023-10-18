-- name: get
SELECT
  g.id,
  g.user_id,
  (
    SELECT username FROM auth_user WHERE id = g.user_id
  ),
  g.title,
  g.description,
  g.access,
  (
    SELECT
      c.name
    FROM
      category c
    WHERE
      c.id = g.category_id
  ) AS category,
  g.views,
  g.date_added,
  g.date_updated,

  g.access_key,
  g.hash,
  g.variations,
  g.active,
  g.ads,
  g.copyright,
  (
    SELECT
      eg.name
    FROM
      generator eg
    WHERE
      eg.id = g.generator_id
  ) AS generator,
  (
	  SELECT
	  	COALESCE(array_agg(DISTINCT egf.name), ARRAY[]::text[])
	  FROM feature egf
	  JOIN generator eg
	  	ON eg.id = egf.generator_id
	  JOIN gen_feature gegf
	  	ON gegf.gen_id = g.id
  ) AS features,
  g.format,
  g.body,
  (
    SELECT
      array_remove(array_agg(s.name), NULL)
    FROM
      gen_subcategory gs
    JOIN subcategory s
      ON s.id = gs.subcategory_id
    WHERE
      g.id = gs.gen_id
  ) AS subcategories,
  (
    SELECT
      array_agg(t.name)
    FROM
      gen_tag gt
    JOIN tag t
      ON t.id = gt.tag_id
    WHERE
      g.id = gt.gen_id
  ) AS tags,
  (
    SELECT
      COALESCE(array_agg(user_id), ARRAY[]::int[])
    FROM
      gen_like
    WHERE
      gen_id = g.id
  ) as likes,
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
      COALESCE(array_agg(user_id), ARRAY[]::int[])
    FROM
      gen_fav
    WHERE
      gen_id = g.id
  ) as favs,
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
JOIN gen_feature gegf
  ON g.id = gegf.gen_id
JOIN feature egf
  ON egf.id = gegf.feature_id
LEFT JOIN category c
  ON c.id = g.category_id
WHERE
  g.id = $1
GROUP BY
  g.id;

-- name: increment_views
UPDATE gen SET views = views + 1 WHERE id = $1;

-- name: get_categories
SELECT
  c.id,
  c.name,
  (SELECT COUNT(1) FROM gen g WHERE g.category_id = c.id) AS count
FROM
  category c
WHERE
  c.id != 99;

-- name: get_other_category
SELECT
	c.id,
	c.name,
	(SELECT COUNT(1) FROM gen g WHERE g.category_id = 99) as count
FROM
	category c
WHERE
  c.id = 99;

-- name: get_subcategories
SELECT
	s.category_id,
	s.name,
	count(1) AS count
FROM gen g
JOIN gen_subcategory gs
	ON gs.gen_id = g.id
JOIN subcategory s
	ON s.id = gs.subcategory_id
JOIN category c
	ON c.id = s.category_id
WHERE g.category_id != 99
GROUP BY s.id, c.name
ORDER BY s.category_id, s.name using ~<~;

-- name: get_tags
SELECT
	t.name,
	COUNT(1) AS count
FROM gen g
JOIN gen_tag gt
	ON gt.gen_id = g.id
JOIN tag t
	ON t.id = gt.tag_id
WHERE g.access = 0
GROUP BY t.id
ORDER BY t.name USING ~<~;

-- name: get_suggestions
SELECT
  g.id,
  g.title,
  (
    SELECT
      count(1)
    FROM
      gen_like
    WHERE
      g.id = gen_id
  ) AS likes_count
FROM
  gen g
WHERE
  g.id IN (
    SELECT
      g.id
    FROM
      gen g
    LEFT JOIN gen_like gl
      ON g.id = gl.gen_id
    GROUP BY g.id
    HAVING COALESCE(COUNT(1), 0) > $1
    ORDER BY g.id
  )
  AND g.access = 0
  AND g.copyright = False
GROUP BY
  g.id;

-- name: get_likes_count
SELECT
	COUNT(1) as count
FROM
	gen g
JOIN gen_like gl
	ON g.id = gl.gen_id
GROUP BY g.id
HAVING g.id = $1;

-- name: get_favs_count
SELECT
	COUNT(1) as count
FROM
	gen g
JOIN gen_fav gf
	ON g.id = gf.gen_id
GROUP BY g.id
HAVING g.id = $1;

-- name: create_vh
INSERT INTO gen_vh(
  gen_id,
  user_id,
  title,
  description,
  access,
  category_id,
  generator_id,
  format,
  body,
  created_at
) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
RETURNING id;

-- name: get_vh
SELECT
  g.*,
  (
    SELECT username FROM auth_user WHERE id = g.user_id
  ),
  (
    SELECT
      c.name
    FROM
      category c
    WHERE
      c.id = g.category_id
  ) AS category,
  (
    SELECT
      eg.name
    FROM
      generator eg
    WHERE
      eg.id = g.generator_id
  ) AS generator,
  (
	  SELECT
	  	COALESCE(array_agg(DISTINCT egf.name), ARRAY[]::text[])
	  FROM feature egf
	  JOIN generator eg
	  	ON eg.id = egf.generator_id
	  JOIN gen_vh_feature gegf
	  	ON gegf.gen_vh_id = g.id
  ) AS features,
  (
    SELECT
      array_remove(array_agg(s.name), NULL)
    FROM
      gen_vh_subcategory gs
    JOIN subcategory s
      ON s.id = gs.subcategory_id
    WHERE
      g.id = gs.gen_vh_id
  ) AS subcategories,
  (
    SELECT
      array_agg(t.name)
    FROM
      gen_vh_tag gt
    JOIN tag t
      ON t.id = gt.tag_id
    WHERE
      g.id = gt.gen_vh_id
  ) AS tags
FROM
  gen_vh g
JOIN gen_vh_feature gegf
  ON g.id = gegf.gen_vh_id
JOIN feature egf
  ON egf.id = gegf.feature_id
LEFT JOIN category c
  ON c.id = g.category_id
WHERE
  g.id = $1;

-- name: get_all_vh
SELECT
  g.*,
  (
    SELECT username FROM auth_user WHERE id = g.user_id
  ),
  (
    SELECT
      c.name
    FROM
      category c
    WHERE
      c.id = g.category_id
  ) AS category,
  (
    SELECT
      eg.name
    FROM
      generator eg
    WHERE
      eg.id = g.generator_id
  ) AS generator,
  (
	  SELECT
	  	COALESCE(array_agg(DISTINCT egf.name), ARRAY[]::text[])
	  FROM feature egf
	  JOIN generator eg
	  	ON eg.id = egf.generator_id
	  JOIN gen_vh_feature gegf
	  	ON gegf.gen_vh_id = g.id
  ) AS features,
  (
    SELECT
      array_remove(array_agg(s.name), NULL)
    FROM
      gen_vh_subcategory gs
    JOIN subcategory s
      ON s.id = gs.subcategory_id
    WHERE
      g.id = gs.gen_vh_id
  ) AS subcategories,
  (
    SELECT
      array_agg(t.name)
    FROM
      gen_vh_tag gt
    JOIN tag t
      ON t.id = gt.tag_id
    WHERE
      g.id = gt.gen_vh_id
  ) AS tags
FROM
  gen_vh g
JOIN gen_vh_feature gegf
  ON g.id = gegf.gen_vh_id
JOIN feature egf
  ON egf.id = gegf.feature_id
LEFT JOIN category c
  ON c.id = g.category_id
JOIN gen cg
  ON g.gen_id = cg.id
WHERE
  g.user_id = $1 AND cg.active = True
GROUP BY
  g.id
ORDER BY g.created_at DESC;

-- name: create
INSERT INTO gen(
    user_id,
    title,
    description,
    category_id,
    access,
    access_key,
    views,
    active,
    ads,
    copyright,
    hash,
    variations,
    date_added,
    date_updated,
    generator_id,
    format,
    body
) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
RETURNING id;

-- name: update
UPDATE gen SET
  title = $2,
  description = $3,
  category_id = $4,
  access = $5,
  hash = $6,
  variations = $7,
  date_updated = COALESCE($8, date_updated),
  generator_id = $9,
  format = $10,
  body = $11
WHERE
  id = $1;

-- name: search_count
SELECT
  COUNT(1)
FROM gen g
WHERE
  ($1::text IS NULL OR g.title iLIKE CONCAT('%', $1::text, '%'))
  AND ($2::text IS NULL OR $2::text = (
    SELECT
      c.name
    FROM
      category c
    WHERE
      c.id = g.category_id
  ))
  AND ($3::text[] IS NULL OR $3::text[] && (
    SELECT
      array_remove(array_agg(s.name), NULL)
    FROM
      gen_subcategory gs
    JOIN subcategory s
      ON s.id = gs.subcategory_id
    WHERE
      g.id = gs.gen_id
  ))
  AND ($4::text[] IS NULL OR $4::text[] && (
    SELECT
      array_agg(t.name)
    FROM
      gen_tag gt
    JOIN tag t
      ON t.id = gt.tag_id
    WHERE
      g.id = gt.gen_id
  ))
  AND ($5::int IS NULL OR g.access = $5::int)
  AND ($6::boolean IS NULL OR g.active = $6::boolean)
;

-- name: search
SELECT
  g.id,
  g.user_id,
  (
    SELECT username FROM auth_user WHERE id = g.user_id
  ),
  g.title,
  g.description,
  g.access,
  (
    SELECT
      c.name
    FROM
      category c
    WHERE
      c.id = g.category_id
  ) AS category,
  g.views,
  g.date_added,
  g.date_updated,

  g.access_key,
  g.hash,
  g.variations,
  g.active,
  g.ads,
  g.copyright,

  (
    SELECT
      eg.name
    FROM
      generator eg
    WHERE
      eg.id = g.generator_id
  ) AS generator,
  (
	  SELECT
	  	COALESCE(array_agg(DISTINCT egf.name), ARRAY[]::text[])
	  FROM feature egf
	  JOIN generator eg
	  	ON eg.id = egf.generator_id
	  JOIN gen_feature gegf
	  	ON gegf.gen_id = g.id
  ) AS features,

  g.format,
  g.body,
  (
    SELECT
      array_remove(array_agg(s.name), NULL)
    FROM
      gen_subcategory gs
    JOIN subcategory s
      ON s.id = gs.subcategory_id
    WHERE
      g.id = gs.gen_id
  ) AS subcategories,
  (
    SELECT
      array_agg(t.name)
    FROM
      gen_tag gt
    JOIN tag t
      ON t.id = gt.tag_id
    WHERE
      g.id = gt.gen_id
  ) AS tags,
  (
    SELECT
      COALESCE(array_agg(user_id), ARRAY[]::int[])
    FROM
      gen_like
    WHERE
      gen_id = g.id
  ) as likes,
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
      COALESCE(array_agg(user_id), ARRAY[]::int[])
    FROM
      gen_fav
    WHERE
      gen_id = g.id
  ) as favs,
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
JOIN gen_feature gegf
  ON g.id = gegf.gen_id
JOIN feature egf
  ON egf.id = gegf.feature_id
LEFT JOIN category c
  ON c.id = g.category_id
JOIN auth_user au
  ON g.user_id = au.id
WHERE
  ($3::text IS NULL OR g.title iLIKE CONCAT('%', $3::text, '%'))
  AND ($4::text IS NULL OR $4::text = (
    SELECT
      c.name
    FROM
      category c
    WHERE
      c.id = g.category_id
  ))
  AND ($5::text[] IS NULL OR $5::text[] && (
    SELECT
      array_remove(array_agg(s.name), NULL)
    FROM
      gen_subcategory gs
    JOIN subcategory s
      ON s.id = gs.subcategory_id
    WHERE
      g.id = gs.gen_id
  ))
  AND ($6::text[] IS NULL OR $6::text[] && (
    SELECT
      array_agg(t.name)
    FROM
      gen_tag gt
    JOIN tag t
      ON t.id = gt.tag_id
    WHERE
      g.id = gt.gen_id
  ))
  AND ($7::int IS NULL OR g.access = $7::int)
  AND ($8::boolean IS NULL OR g.active = $8::boolean)
GROUP BY g.id
ORDER BY {} {}
LIMIT $2::int OFFSET $1::int;


-- name: get_stats
SELECT
  (
    SELECT COUNT(*) FROM gen WHERE active = True
  ) AS active,
  (
    SELECT COUNT(*) FROM gen WHERE active = False
  ) AS inactive,
  (
    SELECT COUNT(*) FROM gen WHERE access = 0
  ) AS public,
  (
    SELECT COUNT(*) FROM gen WHERE access = 1
  ) AS private,
  (
    SELECT COUNT(*) FROM gen WHERE access = 2
  ) AS partly
;
