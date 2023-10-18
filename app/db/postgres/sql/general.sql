-- name: get_info_by_name
SELECT
  *
FROM
  general_info
WHERE
  name = $1;

-- name: get_all_info
SELECT
  *
FROM
  general_info
ORDER BY position ASC;

-- name: get_plot_count
SELECT
  (
    (SELECT count(*) FROM creative_wp)
    +
    (SELECT count(*) FROM creative_plot)
  ) AS checked_count,
  (SELECT count(*) FROM creative_unchecked WHERE name = 'plot') AS not_checked_count
;

-- name: get_general_result
SELECT value FROM {} WHERE id = $1;

-- name: get_creative_result
SELECT value FROM {} OFFSET $1 LIMIT 1;

-- name: get_superpowers
SELECT title, description FROM creative_superpowers OFFSET $1 LIMIT 1;

-- name: toggle_usergen
UPDATE
  general_info
SET
  usergen = NOT usergen
WHERE
  name = $1;

-- name: get_creative_by_value
SELECT value FROM {} WHERE value iLIKE $1;

-- name: suggest
INSERT INTO creative_unchecked(name, value) VALUES ($1, $2);

-- name: get_first_unchecked_usergen
SELECT * FROM creative_unchecked ORDER BY id ASC LIMIT 1;

-- name: get_first_unchecked_wp
SELECT * FROM creative_wp_unchecked ORDER BY id ASC LIMIT 1;

