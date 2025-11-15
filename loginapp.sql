-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: 01 مارس 2025 الساعة 11:52
-- إصدار الخادم: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `loginapp`
--

-- --------------------------------------------------------

--
-- بنية الجدول `accounts`
--

CREATE TABLE `accounts` (
  `id` int(11) NOT NULL,
  `username` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `profile_picture` varchar(255) DEFAULT 'default.png',
  `role` enum('student','teacher','admin') NOT NULL DEFAULT 'student'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `accounts`
--

INSERT INTO `accounts` (`id`, `username`, `email`, `password`, `profile_picture`, `role`) VALUES
(9, 'gg', 'GG@gmail.com', 'scrypt:32768:8:1$qL4sHslofduufQ8e$8583de590f8b4d9b6dc0d0876cb34b4d7c73cb3d59fe674129aeba6e81caa6465c51649101ae1279c703406affec42ecb59fad30a3e21db8b2500cc497db54d1', 'default.png', 'student'),
(10, 'dd', 'dd@gmail.com', 'scrypt:32768:8:1$cag9wjuNVZhDzxvC$cca153a2414b3bed8447fa130b6100f5cc0923576555f7cccee899a254a28884845799b860d4a543c026e1af219f98165de440cfaa52adfbf2708458b2f47ac6', 'IMG-20250220-WA0021.jpg', 'student'),
(11, 'SS', 'SSSy@gmail.com', 'scrypt:32768:8:1$NKeOhMQuqorTQswH$13db19828e6508b7455e8518c4a137bb3e09fdf649260e42d51bd3b16a4fe208023064e8ead06b1efdf1e100f762a64b52e0f6aca2b92c5d192e3c11ea02bc30', 'default.png', 'student'),
(12, 'AA', 'AA@gmail.com', 'scrypt:32768:8:1$SQcw8ITQkFIOdK9D$5ec9998d05f680669dc68ccbb10b3d9f545366681b1b7c074cf763ff27d039af23879a3caf0a5abb89d83f8e44982f1fa5214243d4fde5773ce17b1280fb7f14', 'default.png', 'teacher'),
(13, 'Ibrahim', 'ttttt@hotmail.com', 'scrypt:32768:8:1$UJ6vhgJuEJK7hfS3$2369a38317e767f217a2024161270d8c540a48d5892e7249ae869a9906fb460a3893aa63762746e6153c98f415352f527e5948d651986c3a1e7ebb94780cb99c', '1739368358638.jpg', 'admin'),
(14, 'Ahmed', 'Ahmed@hotmail.com', 'scrypt:32768:8:1$1HIXMSckpTZ3jmVQ$81d69755b80590f87c367386900594994a42ef335fa12720b267c6b17289bf8fc558c400c68af95ba2fd419db7ec68fcdbb3a72f3f0a79128fc94bc4cdae0a96', 'Snapchat-506371119.jpg', 'student'),
(15, 'ali', 'ibrahimalkhoggdoly@gmail.com', 'scrypt:32768:8:1$Gv0ptyvHc2rsTA6f$fb62316a7117c52ee49f770ca056f1dabfa848f96f6fa9e21ef3685315bc87fe9b0a357b9d72c9e7f3f6ab5053b9404702cefa60a0cb72951b3a6f601cdccb4a', 'default.png', 'teacher'),
(16, 'sharf', 'fhgggvff@hotmail.com', 'scrypt:32768:8:1$7Xwuz99vW7jwAvsR$109e19344ce9d50d5b6aec06be2cf791030c139c9c8104dc9f64d7931d5309f540541b303208216e75abad0f5b62e398ccb46f3788a93944ae7996a298518717', 'default.png', 'teacher'),
(17, 'gggg', 'ibrahimalkhgfxdooly@gmail.com', 'scrypt:32768:8:1$G9D2GUGXhO13IGne$72639d2a5ea6b5308dea0795aa5d49840abce0ee0e8e903ba7bedca726e6459453e84ec87c7a4602a1461e33c6864159c8dc65ad5e5b3d01391801e0646ac9d6', 'IMG-20250225-WA0019.jpg', 'student'),
(18, 'Elkhooly', 'hfds@hotmail.com', 'scrypt:32768:8:1$IcIJ7euvDlkwijMM$8723d25b399214b6d25d5b57b186c46e8cbbd16c9d3881bfd7b696c32bf042ffa76f27aeb24e671bcd25ba3eb4f4a9c90ccb76ce0964afd0fcdbed54648e59a5', 'default.png', 'student'),
(19, 'Elshabany', 'dddd@gamil.com', 'scrypt:32768:8:1$g4fGOPFNG9zgQAN0$1aaea47da176550eafd253b6718e83155b5acd5339cbd6fdce91a450aecda54b5bfdd8178a7cde3a93694c17bc4c549ba5ca2aa3b87763a3d189d72c5cefe42e', 'default.png', 'teacher'),
(20, 'mo', 'rgjturu@hotmail.com', 'scrypt:32768:8:1$eUhbKcxBSmjbTLWF$5f7fa2b61b1fa13ef0af6a48ef35f4d62808286e0785b132325b81e4794691ca307c93689a92527f21232c80a86456675b860b72433f0f460222e76318256bef', 'default.png', 'teacher'),
(21, 'ee', 'Ibrahimawewlkhooly@gmail.com', 'scrypt:32768:8:1$S448PHWMRJmT38iS$bad6facab4eca2df80533f7bc580902c3b8b02edfdceca634eba3e6567ede1aa8219f8672f84246b18b8bdc8b782ccbcd0f13d25fc1528828275db7a511626ce', 'default.png', 'student'),
(22, 'hh', 'ibrahimalkhoolyjhgg@gmail.com', 'scrypt:32768:8:1$3i3TH2zTJgMbSVVB$62ec0f0a65b2762fe327d7ef612b7e2a1aa837c234355a439ba5b10696420fd93eebfff05d90148100517145504c0eeb2231c22a2622cdf0bcdf1beb069c3025', 'scrypt:32768:8:1$PGlmtdv2B9VTrU1N$88a63cdf4b69d110fad9b06a46eb373fac3c6a4576c602195246c8256747bf33dc3934a07d7e1e8450362e35327890afe55a1776793231ddca556b1a1d85f28e', 'student'),
(23, 'fg', 'gdfgg@hotmail.com', 'scrypt:32768:8:1$WkrQccwjykaQN6iq$bdce3420387a92e2a718cb6851297b81eaeacd21b7d1395ef8dd67329bc3244382897c30e2eb29331aa4b2fc9f3170d873a837f1725032553d4d7397fa6f2d9f', 'default.png', 'student'),
(24, 'ad', '4a5t6y@gmail.com', 'scrypt:32768:8:1$3SBL7nvqT8wDv49Q$378c0e838aef174d490a3d6b0ca22584dcaade3b2153f7005f5696054d107af696c0aafd09df4bd97a050dce36c9a91298ea1ac13007f7479ac92b038db8978f', 'default.png', 'teacher'),
(25, 'F', 'hcj@gmail.com', 'scrypt:32768:8:1$PBLsiJfy39AE5qqb$126e4c9f92cca8d3b96ee7dc177412cdfbd79b78b7fbde35c999f896f91a90c74c515779ffd2ac109b2e39e4519a6509de2336284d54a90845251001fd68f2e7', 'default.png', 'student');

-- --------------------------------------------------------

--
-- بنية الجدول `activity_logs`
--

CREATE TABLE `activity_logs` (
  `id` int(11) NOT NULL,
  `activity` varchar(255) NOT NULL,
  `username` varchar(50) NOT NULL,
  `user_id` int(11) NOT NULL,
  `date` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `activity_logs`
--

INSERT INTO `activity_logs` (`id`, `activity`, `username`, `user_id`, `date`) VALUES
(99, 'User updated profile', 'alii', 15, '2025-02-25 19:05:42'),
(100, 'User updated profile', 'ali', 15, '2025-02-25 19:05:57'),
(101, 'User updated profile', 'gggg', 17, '2025-02-25 19:07:29'),
(102, 'User updated profile', 'gggg', 17, '2025-02-25 19:08:16'),
(103, 'User updated profile', 'gggg', 17, '2025-02-25 19:16:43'),
(104, 'New user registered', 'uu', 22, '2025-02-25 19:29:04'),
(105, 'User updated profile', 'uu', 22, '2025-02-25 19:58:55'),
(106, 'User updated profile', 'uu', 22, '2025-02-25 20:07:45'),
(107, 'User updated profile', 'uu', 22, '2025-02-25 20:11:19'),
(108, 'User updated profile', 'gggg', 17, '2025-02-25 20:23:03'),
(109, 'User updated profile', 'gggg', 17, '2025-02-25 20:24:21'),
(110, 'User updated profile', 'gggg', 17, '2025-02-25 20:32:07'),
(111, 'User updated profile', 'gggg', 17, '2025-02-25 21:26:11'),
(112, 'User updated profile', 'gggg', 17, '2025-02-25 21:32:20'),
(113, 'User updated profile', 'gggg', 17, '2025-02-25 21:35:34'),
(114, 'User updated profile', 'gggg', 17, '2025-02-25 21:35:57'),
(115, 'User updated profile', 'gggg', 17, '2025-02-25 21:39:18'),
(116, 'User updated profile', 'gggg', 17, '2025-02-25 21:48:01'),
(117, 'User updated profile', 'gggg', 17, '2025-02-25 21:49:44'),
(118, 'User updated profile', 'gggg', 17, '2025-02-25 21:50:55'),
(119, 'User updated profile', 'sharf', 16, '2025-02-26 17:12:29'),
(120, 'User updated profile', 'sharf', 16, '2025-02-26 17:13:09'),
(121, 'New user registered', 'fg', 23, '2025-02-26 20:57:39'),
(122, 'New user registered', 'ad', 24, '2025-02-26 21:29:33'),
(123, 'New user registered', 'F', 25, '2025-02-26 21:29:55');

-- --------------------------------------------------------

--
-- بنية الجدول `answers`
--

CREATE TABLE `answers` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `question_id` int(11) DEFAULT NULL,
  `user_answer` text NOT NULL,
  `is_correct` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `answers`
--

INSERT INTO `answers` (`id`, `user_id`, `question_id`, `user_answer`, `is_correct`) VALUES
(1, 16, 1, 'true', 0),
(2, 16, 2, 'نبب', 0),
(3, 16, 1, 'true', 0),
(4, 16, 2, 'نلىون', 0),
(5, 16, 1, 'true', 0),
(6, 16, 2, 'نبب', 0),
(7, 16, 1, 'false', 0),
(8, 16, 2, 'نبب', 0),
(9, 16, 1, 'false', 0),
(10, 16, 2, 'نلىون', 0),
(11, 16, 3, 'true', 1),
(12, 16, 3, 'false', 0),
(13, 16, 3, 'true', 0),
(14, 22, 5, 'true', 1),
(15, 23, 6, 'false', 0),
(17, 25, 8, 'ي', 1),
(18, 13, 8, 'ب', 0);

-- --------------------------------------------------------

--
-- بنية الجدول `choices`
--

CREATE TABLE `choices` (
  `id` int(11) NOT NULL,
  `question_id` int(11) DEFAULT NULL,
  `choice_text` text NOT NULL,
  `choice_order` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `choices`
--

INSERT INTO `choices` (`id`, `question_id`, `choice_text`, `choice_order`) VALUES
(1, 2, 'نلىون', NULL),
(2, 2, 'نبب', NULL),
(3, 2, 'نلبغ', NULL),
(4, 2, 'درودم', NULL),
(5, 8, 'ثي', NULL),
(6, 8, 'ي', NULL),
(7, 8, 'ب', NULL),
(8, 8, 'لر', NULL);

-- --------------------------------------------------------

--
-- بنية الجدول `comments`
--

CREATE TABLE `comments` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `post_id` int(11) NOT NULL,
  `content` text NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `comments`
--

INSERT INTO `comments` (`id`, `user_id`, `post_id`, `content`, `timestamp`) VALUES
(1, 23, 1, 'xgh', '2025-02-26 18:58:09'),
(2, 25, 2, 'Nfjb', '2025-02-26 19:39:41');

-- --------------------------------------------------------

--
-- بنية الجدول `exams`
--

CREATE TABLE `exams` (
  `id` int(11) NOT NULL,
  `subject_id` int(11) DEFAULT NULL,
  `exam_name` varchar(255) NOT NULL,
  `num_questions` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `description` text DEFAULT NULL,
  `is_visible` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `exams`
--

INSERT INTO `exams` (`id`, `subject_id`, `exam_name`, `num_questions`, `created_at`, `description`, `is_visible`) VALUES
(3, 1, 'دنوو', 0, '2025-02-24 23:42:11', 'نوةا', 1),
(4, 5, 'gghkh', 0, '2025-02-26 19:04:58', 'oiuytggkh', 1),
(5, 6, 'ميد ', 0, '2025-02-26 19:34:21', 'كمنتا', 0);

-- --------------------------------------------------------

--
-- بنية الجدول `exam_questions`
--

CREATE TABLE `exam_questions` (
  `id` int(11) NOT NULL,
  `exam_id` int(11) DEFAULT NULL,
  `question_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `exam_questions`
--

INSERT INTO `exam_questions` (`id`, `exam_id`, `question_id`) VALUES
(5, 3, 5),
(6, 4, 6),
(8, 5, 8);

-- --------------------------------------------------------

--
-- بنية الجدول `friends`
--

CREATE TABLE `friends` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `friend_id` int(11) NOT NULL,
  `status` enum('pending','accepted') DEFAULT 'pending'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `friends`
--

INSERT INTO `friends` (`id`, `user_id`, `friend_id`, `status`) VALUES
(1, 10, 9, 'pending'),
(2, 10, 11, 'accepted'),
(3, 12, 11, 'pending'),
(4, 12, 9, 'pending'),
(5, 12, 10, 'accepted'),
(7, 13, 10, 'accepted'),
(8, 12, 13, 'accepted'),
(9, 14, 13, 'accepted'),
(10, 13, 13, 'accepted'),
(11, 10, 14, 'accepted'),
(12, 15, 13, 'accepted'),
(13, 14, 15, 'accepted'),
(14, 16, 13, 'accepted'),
(15, 18, 15, 'accepted'),
(16, 19, 15, 'accepted'),
(17, 19, 13, 'accepted'),
(18, 19, 18, 'accepted'),
(19, 20, 13, 'accepted'),
(20, 16, 9, 'pending'),
(21, 16, 10, 'pending'),
(22, 16, 11, 'pending'),
(23, 16, 12, 'pending'),
(24, 16, 14, 'pending'),
(25, 16, 18, 'pending'),
(26, 16, 19, 'pending'),
(27, 16, 20, 'pending'),
(28, 16, 21, 'pending'),
(29, 15, 9, 'pending'),
(30, 23, 15, 'accepted'),
(31, 25, 24, 'accepted');

-- --------------------------------------------------------

--
-- بنية الجدول `likes`
--

CREATE TABLE `likes` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `post_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `likes`
--

INSERT INTO `likes` (`id`, `user_id`, `post_id`) VALUES
(1, 16, 1),
(3, 23, 1),
(4, 25, 2);

-- --------------------------------------------------------

--
-- بنية الجدول `messages`
--

CREATE TABLE `messages` (
  `id` int(11) NOT NULL,
  `sender_id` int(11) NOT NULL,
  `receiver_id` int(11) NOT NULL,
  `message` text NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `messages`
--

INSERT INTO `messages` (`id`, `sender_id`, `receiver_id`, `message`, `timestamp`) VALUES
(1, 16, 14, 'ناب', '2025-02-24 23:45:21'),
(2, 23, 15, 'jvjvhx', '2025-02-26 18:59:12'),
(3, 15, 23, 'ةممةتي', '2025-02-26 18:59:19'),
(4, 24, 25, 'نتال', '2025-02-26 19:40:48'),
(5, 25, 24, 'Nfvsg', '2025-02-26 19:40:56'),
(6, 24, 25, 'ممم', '2025-02-26 19:41:01'),
(7, 13, 20, 'OIUYT', '2025-02-26 19:41:38');

-- --------------------------------------------------------

--
-- بنية الجدول `posts`
--

CREATE TABLE `posts` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `content` text NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `posts`
--

INSERT INTO `posts` (`id`, `user_id`, `content`, `timestamp`) VALUES
(1, 13, 'ىتلهل', '2025-02-24 23:32:55'),
(2, 23, 'ufufigif', '2025-02-26 18:58:29'),
(3, 25, 'Jfggdky', '2025-02-26 19:40:07');

-- --------------------------------------------------------

--
-- بنية الجدول `questions`
--

CREATE TABLE `questions` (
  `id` int(11) NOT NULL,
  `subject_id` int(11) DEFAULT NULL,
  `question_text` text NOT NULL,
  `question_type` enum('mcq','true_false') NOT NULL,
  `correct_answer` text NOT NULL,
  `exam_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `questions`
--

INSERT INTO `questions` (`id`, `subject_id`, `question_text`, `question_type`, `correct_answer`, `exam_id`) VALUES
(1, NULL, 'ماةر', 'true_false', '', 0),
(2, NULL, 'ظرنمم', 'mcq', '', 0),
(3, NULL, 'ظننت', 'true_false', '', 0),
(5, NULL, 'كناة', 'true_false', 'true', 0),
(6, NULL, 'oiuytgdgh', 'true_false', '', 0),
(8, NULL, 'صثصصص', 'mcq', '', 0);

-- --------------------------------------------------------

--
-- بنية الجدول `student_grades`
--

CREATE TABLE `student_grades` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `exam_id` int(11) NOT NULL,
  `score` int(11) NOT NULL,
  `total_questions` int(11) NOT NULL,
  `grade_date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `student_grades`
--

INSERT INTO `student_grades` (`id`, `user_id`, `exam_id`, `score`, `total_questions`, `grade_date`) VALUES
(9, 22, 3, 1, 1, '0000-00-00'),
(10, 23, 4, 0, 1, '0000-00-00'),
(11, 25, 5, 1, 2, '0000-00-00'),
(12, 13, 5, 0, 1, '0000-00-00');

-- --------------------------------------------------------

--
-- بنية الجدول `subjects`
--

CREATE TABLE `subjects` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `teacher` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `subjects`
--

INSERT INTO `subjects` (`id`, `name`, `teacher`, `description`, `created_at`) VALUES
(1, 'عربي', 'sharf', 'تلب', '2025-02-24 23:34:09'),
(2, 'ظةنم', 'sharf', 'دتةى', '2025-02-24 23:41:36'),
(3, 'ىعلع', 'sharf', 'عرغ', '2025-02-24 23:53:36'),
(4, 'غبع', 'ali', 'تر', '2025-02-26 18:47:40'),
(5, 'hgdgh', 'ali', 'iuyt', '2025-02-26 19:04:05'),
(6, 'فرنساوي', 'ad', 'فغتهحخ', '2025-02-26 19:33:03');

-- --------------------------------------------------------

--
-- بنية الجدول `subject_files`
--

CREATE TABLE `subject_files` (
  `id` int(11) NOT NULL,
  `subject_id` int(11) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `filetype` varchar(50) NOT NULL,
  `uploaded_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- إرجاع أو استيراد بيانات الجدول `subject_files`
--

INSERT INTO `subject_files` (`id`, `subject_id`, `filename`, `filetype`, `uploaded_at`) VALUES
(1, 1, 'lv_7405838544675081528_.mp4', 'mp4', '2025-02-24 23:34:52'),
(2, 6, 'Report1.pdf', 'pdf', '2025-02-26 19:33:49');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `accounts`
--
ALTER TABLE `accounts`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `answers`
--
ALTER TABLE `answers`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `question_id` (`question_id`);

--
-- Indexes for table `choices`
--
ALTER TABLE `choices`
  ADD PRIMARY KEY (`id`),
  ADD KEY `question_id` (`question_id`);

--
-- Indexes for table `comments`
--
ALTER TABLE `comments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `post_id` (`post_id`);

--
-- Indexes for table `exams`
--
ALTER TABLE `exams`
  ADD PRIMARY KEY (`id`),
  ADD KEY `subject_id` (`subject_id`);

--
-- Indexes for table `exam_questions`
--
ALTER TABLE `exam_questions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `exam_id` (`exam_id`),
  ADD KEY `question_id` (`question_id`);

--
-- Indexes for table `friends`
--
ALTER TABLE `friends`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `friend_id` (`friend_id`);

--
-- Indexes for table `likes`
--
ALTER TABLE `likes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_like` (`user_id`,`post_id`),
  ADD KEY `post_id` (`post_id`);

--
-- Indexes for table `messages`
--
ALTER TABLE `messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `sender_id` (`sender_id`),
  ADD KEY `receiver_id` (`receiver_id`);

--
-- Indexes for table `posts`
--
ALTER TABLE `posts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `questions`
--
ALTER TABLE `questions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `subject_id` (`subject_id`);

--
-- Indexes for table `student_grades`
--
ALTER TABLE `student_grades`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `exam_id` (`exam_id`);

--
-- Indexes for table `subjects`
--
ALTER TABLE `subjects`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `subject_files`
--
ALTER TABLE `subject_files`
  ADD PRIMARY KEY (`id`),
  ADD KEY `subject_id` (`subject_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `accounts`
--
ALTER TABLE `accounts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;

--
-- AUTO_INCREMENT for table `activity_logs`
--
ALTER TABLE `activity_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=124;

--
-- AUTO_INCREMENT for table `answers`
--
ALTER TABLE `answers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `choices`
--
ALTER TABLE `choices`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `comments`
--
ALTER TABLE `comments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `exams`
--
ALTER TABLE `exams`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `exam_questions`
--
ALTER TABLE `exam_questions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `friends`
--
ALTER TABLE `friends`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=32;

--
-- AUTO_INCREMENT for table `likes`
--
ALTER TABLE `likes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `messages`
--
ALTER TABLE `messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `posts`
--
ALTER TABLE `posts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `questions`
--
ALTER TABLE `questions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `student_grades`
--
ALTER TABLE `student_grades`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `subjects`
--
ALTER TABLE `subjects`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `subject_files`
--
ALTER TABLE `subject_files`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- قيود الجداول المُلقاة.
--

--
-- قيود الجداول `answers`
--
ALTER TABLE `answers`
  ADD CONSTRAINT `answers_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `accounts` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `answers_ibfk_2` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE;

--
-- قيود الجداول `choices`
--
ALTER TABLE `choices`
  ADD CONSTRAINT `choices_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE;

--
-- قيود الجداول `comments`
--
ALTER TABLE `comments`
  ADD CONSTRAINT `comments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `accounts` (`id`),
  ADD CONSTRAINT `comments_ibfk_2` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`);

--
-- قيود الجداول `exams`
--
ALTER TABLE `exams`
  ADD CONSTRAINT `exams_ibfk_1` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`) ON DELETE CASCADE;

--
-- قيود الجداول `exam_questions`
--
ALTER TABLE `exam_questions`
  ADD CONSTRAINT `exam_questions_ibfk_1` FOREIGN KEY (`exam_id`) REFERENCES `exams` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `exam_questions_ibfk_2` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE;

--
-- قيود الجداول `friends`
--
ALTER TABLE `friends`
  ADD CONSTRAINT `friends_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `accounts` (`id`),
  ADD CONSTRAINT `friends_ibfk_2` FOREIGN KEY (`friend_id`) REFERENCES `accounts` (`id`);

--
-- قيود الجداول `likes`
--
ALTER TABLE `likes`
  ADD CONSTRAINT `likes_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `accounts` (`id`),
  ADD CONSTRAINT `likes_ibfk_2` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`);

--
-- قيود الجداول `messages`
--
ALTER TABLE `messages`
  ADD CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `accounts` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `accounts` (`id`) ON DELETE CASCADE;

--
-- قيود الجداول `posts`
--
ALTER TABLE `posts`
  ADD CONSTRAINT `posts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `accounts` (`id`) ON DELETE CASCADE;

--
-- قيود الجداول `questions`
--
ALTER TABLE `questions`
  ADD CONSTRAINT `questions_ibfk_1` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`) ON DELETE CASCADE;

--
-- قيود الجداول `student_grades`
--
ALTER TABLE `student_grades`
  ADD CONSTRAINT `student_grades_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `accounts` (`id`),
  ADD CONSTRAINT `student_grades_ibfk_2` FOREIGN KEY (`exam_id`) REFERENCES `exams` (`id`);

--
-- قيود الجداول `subject_files`
--
ALTER TABLE `subject_files`
  ADD CONSTRAINT `subject_files_ibfk_1` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
