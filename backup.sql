-- MySQL dump 10.13  Distrib 9.4.0, for Win64 (x86_64)
--
-- Host: localhost    Database: beds_and_vaccine_bookings
-- ------------------------------------------------------
-- Server version	9.4.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `audit_logs`
--

DROP TABLE IF EXISTS `audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_logs` (
  `Log_ID` int NOT NULL AUTO_INCREMENT,
  `User_ID` int NOT NULL,
  `Table_Name` varchar(30) DEFAULT NULL,
  `Record_ID` int DEFAULT NULL,
  `Details` varchar(100) DEFAULT NULL,
  `Timestamp` datetime DEFAULT NULL,
  PRIMARY KEY (`Log_ID`),
  KEY `User_ID` (`User_ID`),
  CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`User_ID`) REFERENCES `users` (`User_ID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_logs`
--

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
INSERT INTO `audit_logs` VALUES (1,7,'beds',29,'CREATED: Added bed type General with status booked','2025-10-22 12:48:03'),(2,7,'vaccines',3,'CREATED: Added covaxin slot on 2025-10-10 at 13:00','2025-10-22 12:48:25'),(3,7,'vaccines',3,'UPDATED: covaxin(2025-10-10 13:00:00)->covaxin(2025-10-10 13:00:00)','2025-10-22 13:10:51'),(4,8,'bookings',19,'CREATED: Vaccine 2 booked','2025-10-22 14:02:04'),(5,8,'bookings',20,'CREATED: Vaccine 2 booked','2025-10-22 14:02:43'),(6,8,'bookings',21,'CREATED: Vaccine 3 booked','2025-10-22 14:03:50'),(7,8,'bookings',22,'CREATED: Vaccine 3 booked','2025-10-22 14:04:46'),(8,8,'bookings',23,'CREATED: Vaccine 3 booked','2025-10-22 14:05:41'),(9,8,'bookings',24,'CREATED: Vaccine 3 booked','2025-10-22 14:06:55'),(10,8,'bookings',25,'CREATED: Vaccine 2 booked','2025-10-22 14:10:12'),(11,8,'bookings',26,'CREATED: Vaccine 2 booked','2025-10-22 14:11:33'),(12,8,'bookings',27,'CREATED: Vaccine 2 booked','2025-10-22 14:12:29'),(13,7,'beds',28,'UPDATED: Type General->General, Status available->available','2025-10-24 04:46:15'),(14,7,'bookings',24,'UPDATED: Status: confirmed -> Completed','2025-10-24 04:49:28'),(15,7,'beds',28,'DELETED: Deleted bed type General','2025-10-24 04:49:59'),(16,7,'beds',29,'UPDATED: Type General->General, Status booked->booked','2025-10-24 04:50:04'),(17,7,'beds',30,'CREATED: Added bed type Private with status available','2025-10-24 04:50:13'),(18,7,'beds',30,'DELETED: Deleted bed type Private','2025-10-24 04:50:15'),(19,7,'vaccines',4,'CREATED: Added Chickenpox slot on 2024-11-11 at 12:40','2025-10-24 04:52:13'),(20,7,'beds',31,'CREATED: Added bed type Private with status available','2025-10-24 05:00:15'),(21,7,'beds',31,'DELETED: Deleted bed type Private','2025-10-24 05:02:21'),(22,7,'vaccines',4,'DELETED: Deleted Chickenpox slot','2025-10-24 05:02:54');
/*!40000 ALTER TABLE `audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `beds`
--

DROP TABLE IF EXISTS `beds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `beds` (
  `Bed_ID` int NOT NULL AUTO_INCREMENT,
  `Hospital_ID` int NOT NULL,
  `Bed_Type` varchar(20) DEFAULT NULL,
  `Status` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`Bed_ID`),
  KEY `Hospital_ID` (`Hospital_ID`),
  CONSTRAINT `beds_ibfk_1` FOREIGN KEY (`Hospital_ID`) REFERENCES `hospitals` (`Hospital_ID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `beds`
--

LOCK TABLES `beds` WRITE;
/*!40000 ALTER TABLE `beds` DISABLE KEYS */;
INSERT INTO `beds` VALUES (1,1,'ICU','reserved'),(2,1,'General','reserved'),(3,1,'Private','reserved'),(4,2,'ICU','reserved'),(5,2,'General','reserved'),(6,2,'Private','reserved'),(17,101,'General','Available'),(18,101,'ICU','Occupied'),(19,102,'Maternity','Available'),(20,102,'Pediatric','Occupied'),(21,103,'Emergency','Available'),(22,103,'VIP','Available'),(23,104,'Isolation','Occupied'),(24,104,'General','Available'),(26,106,'Pediatric','Available'),(29,105,'General','booked');
/*!40000 ALTER TABLE `beds` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bookings`
--

DROP TABLE IF EXISTS `bookings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bookings` (
  `Booking_ID` int NOT NULL AUTO_INCREMENT,
  `User_ID` int NOT NULL,
  `Bed_ID` int DEFAULT NULL,
  `Vaccine_ID` int DEFAULT NULL,
  `Booking_Type` varchar(10) DEFAULT NULL,
  `Booking_date` date DEFAULT NULL,
  `Appointment_date` date DEFAULT NULL,
  `Status` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`Booking_ID`),
  KEY `User_ID` (`User_ID`),
  KEY `bookings_ibfk_2` (`Bed_ID`),
  KEY `bookings_ibfk_slot` (`Vaccine_ID`),
  CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`User_ID`) REFERENCES `users` (`User_ID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `bookings_ibfk_2` FOREIGN KEY (`Bed_ID`) REFERENCES `beds` (`Bed_ID`),
  CONSTRAINT `bookings_ibfk_slot` FOREIGN KEY (`Vaccine_ID`) REFERENCES `vaccines` (`Slot_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bookings`
--

LOCK TABLES `bookings` WRITE;
/*!40000 ALTER TABLE `bookings` DISABLE KEYS */;
INSERT INTO `bookings` VALUES (1,1,1,NULL,'bed','2025-10-09','2025-10-09','confirmed'),(2,1,1,NULL,'bed','2025-10-09','2025-10-09','confirmed'),(3,1,5,NULL,'bed','2025-10-09','2025-10-09','confirmed'),(4,1,2,NULL,'bed','2025-10-09','2025-10-09','confirmed'),(5,1,6,NULL,'bed','2025-10-09','2025-10-09','confirmed'),(6,1,3,NULL,'bed','2025-10-09','2025-10-09','confirmed'),(7,1,NULL,1,'vaccine','2025-10-09','2025-10-10','confirmed'),(8,1,NULL,1,'vaccine','2025-10-09','2025-10-10','confirmed'),(9,1,NULL,1,'vaccine','2025-10-09','2025-10-10','confirmed'),(10,1,NULL,1,'vaccine','2025-10-09','2025-10-10','confirmed'),(11,1,NULL,1,'vaccine','2025-10-09','2025-10-10','confirmed'),(12,1,NULL,1,'vaccine','2025-10-09','2025-10-10','confirmed'),(13,1,NULL,1,'vaccine','2025-10-09','2025-10-10','confirmed'),(14,1,NULL,1,'vaccine','2025-10-09','2025-10-10','confirmed'),(15,1,NULL,1,'vaccine','2025-10-09','2025-10-10','confirmed'),(16,1,NULL,1,'vaccine','2025-10-09','2025-10-10','confirmed'),(17,8,NULL,2,'vaccine','2025-10-22','2025-10-10','Completed'),(18,8,NULL,2,'vaccine','2025-10-22','2025-10-10','confirmed'),(19,8,NULL,2,'vaccine','2025-10-22','2025-10-10','Cancelled'),(20,8,NULL,2,'vaccine','2025-10-22','2025-10-10','confirmed'),(21,8,NULL,3,'vaccine','2025-10-22','2025-10-10','confirmed'),(22,8,NULL,3,'vaccine','2025-10-22','2025-10-10','confirmed'),(23,8,NULL,3,'vaccine','2025-10-22','2025-10-10','confirmed'),(24,8,NULL,3,'vaccine','2025-10-22','2025-10-10','Completed'),(25,8,NULL,2,'vaccine','2025-10-22','2025-10-10','confirmed'),(26,8,NULL,2,'vaccine','2025-10-22','2025-10-10','confirmed'),(27,8,NULL,2,'vaccine','2025-10-22','2025-10-10','confirmed'),(28,8,NULL,2,'vaccine','2025-10-22','2025-10-10','confirmed'),(29,8,NULL,2,'vaccine','2025-10-23','2025-10-10','confirmed'),(30,8,NULL,2,'vaccine','2025-10-23','2025-10-10','Cancelled'),(31,8,NULL,3,'Vaccine','2025-10-23','2025-10-10','Confirmed'),(32,8,NULL,3,'Vaccine','2025-10-23','2025-10-10','Confirmed'),(33,8,NULL,3,'Vaccine','2025-10-23','2025-10-10','Confirmed'),(34,8,NULL,2,'Vaccine','2025-10-23','2025-10-10','Confirmed'),(35,7,NULL,2,'Vaccine','2025-10-24','2025-10-10','Confirmed');
/*!40000 ALTER TABLE `bookings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `hospitals`
--

DROP TABLE IF EXISTS `hospitals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `hospitals` (
  `Hospital_ID` int NOT NULL AUTO_INCREMENT,
  `Name` varchar(50) NOT NULL,
  `Street_Address` varchar(100) NOT NULL,
  `City` varchar(30) NOT NULL,
  `State` varchar(30) NOT NULL,
  `Postal_Code` varchar(20) NOT NULL,
  `Phone` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`Hospital_ID`),
  UNIQUE KEY `Phone` (`Phone`)
) ENGINE=InnoDB AUTO_INCREMENT=107 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `hospitals`
--

LOCK TABLES `hospitals` WRITE;
/*!40000 ALTER TABLE `hospitals` DISABLE KEYS */;
INSERT INTO `hospitals` VALUES (101,'Apollo Hospital','Opposite Pune Central Mall, Camp','Pune','Maharashtra','411001','020-12345678'),(102,'Sahyadri Hospital','5th Main, Bund Garden Road','Pune','Maharashtra','411042','020-23456789'),(103,'Ruby Hall Clinic','2nd Floor, Senapati Bapat Road','Pune','Maharashtra','411016','020-34567890'),(104,'Jehangir Hospital','Marinagar, Jangli Maharaj Road','Pune','Maharashtra','411004','020-45678901'),(105,'Aditya Birla Hospital','Kothrud, Pune','Pune','Maharashtra','411038','020-56789012'),(106,'Deenanath Mangeshkar Hospital','Erandwane, Pune','Pune','Maharashtra','411004','020-67890123');
/*!40000 ALTER TABLE `hospitals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments`
--

DROP TABLE IF EXISTS `payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments` (
  `Payment_ID` int NOT NULL AUTO_INCREMENT,
  `User_ID` int NOT NULL,
  `Booking_ID` int NOT NULL,
  `Booking_Type` varchar(10) DEFAULT NULL,
  `Amount` decimal(10,2) DEFAULT NULL,
  `Payment_Method` varchar(20) DEFAULT NULL,
  `Payment_Status` varchar(20) DEFAULT NULL,
  `Payment_Date` datetime DEFAULT NULL,
  PRIMARY KEY (`Payment_ID`),
  KEY `User_ID` (`User_ID`),
  KEY `payments_ibfk_2` (`Booking_ID`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`User_ID`) REFERENCES `users` (`User_ID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `payments_ibfk_2` FOREIGN KEY (`Booking_ID`) REFERENCES `bookings` (`Booking_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments`
--

LOCK TABLES `payments` WRITE;
/*!40000 ALTER TABLE `payments` DISABLE KEYS */;
INSERT INTO `payments` VALUES (1,1,5,'bed',3000.00,'UPI','completed','2025-10-09 19:30:49'),(2,1,6,'bed',3000.00,'Credit Card','completed','2025-10-09 19:33:47');
/*!40000 ALTER TABLE `payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `User_ID` int NOT NULL AUTO_INCREMENT,
  `Full_Name` varchar(50) NOT NULL,
  `Email` varchar(100) NOT NULL,
  `Phone` varchar(20) DEFAULT NULL,
  `Password` varchar(255) DEFAULT NULL,
  `Role` varchar(20) NOT NULL,
  `Gender` varchar(10) DEFAULT NULL,
  `DOB` date DEFAULT NULL,
  `Hospital_ID` int DEFAULT NULL,
  PRIMARY KEY (`User_ID`),
  UNIQUE KEY `Email` (`Email`),
  UNIQUE KEY `Phone` (`Phone`),
  KEY `Hospital_ID` (`Hospital_ID`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`Hospital_ID`) REFERENCES `hospitals` (`Hospital_ID`) ON DELETE SET NULL,
  CONSTRAINT `users_chk_1` CHECK ((`Role` in (_utf8mb4'patient',_utf8mb4'staff'))),
  CONSTRAINT `users_chk_2` CHECK ((`Gender` in (_utf8mb4'Male',_utf8mb4'Female',_utf8mb4'Other')))
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (4,'asdfg','shr@greenvalley.com',NULL,'scrypt:32768:8:1$VMWylkWIaHedTcZP$d06522df9e9536293e22408b135791279908369edb0078d499989e58db921b4c508b5d6bf4d7cdec35e16b2686d228ef55c406a1f9836f23b963771ea26d3e2a','patient',NULL,NULL,NULL),(7,'shruti','shruti2019@gmail.com','123456789','scrypt:32768:8:1$i2VXmuzGtSHpusJu$ca3b431b0405e8d4527a4e7819c9036892a64ee51b4873e57516285a10cec681e9d88f7e1d9339a5b3f9acf9a1282a77461b2385448b5f3b12e1cba8edd22940','staff',NULL,NULL,105),(8,'abcd','abc@gmail.com','1234567890','scrypt:32768:8:1$HfKXsUuA9tE8UMNc$3b26cd08d0f864a94d09fed22775e07cf4e937fca2bc40da361676ea9f088cadca331e41862d6fa1cff5355d550effe7e1847c7e1236c60565abc71839bd5ed4','patient','Female','2005-08-10',NULL);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vaccines`
--

DROP TABLE IF EXISTS `vaccines`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vaccines` (
  `Slot_ID` int NOT NULL AUTO_INCREMENT,
  `Hospital_ID` int NOT NULL,
  `Vaccine_Name` varchar(50) DEFAULT NULL,
  `Slot_Date` date DEFAULT NULL,
  `Slot_Time` time DEFAULT NULL,
  `Capacity` int DEFAULT NULL,
  `Available` int DEFAULT NULL,
  PRIMARY KEY (`Slot_ID`),
  KEY `Hospital_ID` (`Hospital_ID`),
  CONSTRAINT `vaccines_ibfk_1` FOREIGN KEY (`Hospital_ID`) REFERENCES `hospitals` (`Hospital_ID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vaccines`
--

LOCK TABLES `vaccines` WRITE;
/*!40000 ALTER TABLE `vaccines` DISABLE KEYS */;
INSERT INTO `vaccines` VALUES (1,1,'Covishield','2025-10-10','10:00:00',10,0),(2,105,'Hepatitist A','2025-10-10','12:00:00',40,8),(3,105,'covaxin','2025-10-10','13:00:00',56,43);
/*!40000 ALTER TABLE `vaccines` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-10-24 10:40:47
